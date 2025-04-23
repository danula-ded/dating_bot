import logging.config
import asyncio

import msgpack

from consumer.handlers.registration import handle_registration
from consumer.handlers.upload_file import upload_file_handler
from consumer.handlers.show_file import show_files
from consumer.handlers.profile_update import handle_profile_update
from consumer.logger import LOGGING_CONFIG, correlation_id_ctx, logger
from consumer.metrics import TOTAL_RECEIVED_MESSAGES
from consumer.schema.registration import RegistrationMessage
from consumer.schema.file import FileMessage
from consumer.storage import rabbit


async def start_consumer() -> None:
    logging.config.dictConfig(LOGGING_CONFIG)
    logger.info('Starting consumer...')

    queue_name = 'user_messages'
    async with rabbit.channel_pool.acquire() as channel:
        # Will take no more than 10 messages in advance
        await channel.set_qos(prefetch_count=10)

        # Declaring queue
        queue = await channel.declare_queue(queue_name, durable=True)

        logger.info('Consumer started!')
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                TOTAL_RECEIVED_MESSAGES.inc()
                async with message.process():
                    # Set correlation_id if available, otherwise use a default
                    correlation_id = message.correlation_id or 'default_correlation_id'
                    correlation_id_ctx.set(correlation_id)

                    try:
                        # Try to unpack as FileMessage first
                        try:
                            body: FileMessage = FileMessage.model_validate(msgpack.unpackb(message.body))
                            logger.info('File message received: %s', body)

                            if body.action == 'upload_file':
                                await upload_file_handler(body)
                            elif body.action == 'show_files_user':
                                await show_files(body)
                            else:
                                logger.warning('Unknown file action: %s', body.action)

                        except Exception:
                            # If not FileMessage, try as RegistrationMessage
                            try:
                                body: RegistrationMessage = RegistrationMessage.model_validate(msgpack.unpackb(message.body))
                                logger.info('Registration message received: %s', body)

                                if body.action == 'user_registration':
                                    await handle_registration(body)
                                else:
                                    logger.warning('Unknown registration action: %s', body.action)

                            except Exception:
                                # If not RegistrationMessage, try as profile update
                                try:
                                    body = msgpack.unpackb(message.body)
                                    if isinstance(body, dict) and 'action' in body and body['action'] == 'profile_update':
                                        await handle_profile_update(body)
                                    else:
                                        logger.warning('Unknown message type: %s', body)
                                except Exception as e:
                                    logger.error('Failed to parse message: %s', e)
                                    continue

                    except Exception as e:
                        logger.error('Error processing message: %s', e)
                        continue
