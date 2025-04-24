import logging.config
import asyncio

import msgpack
import aio_pika

from consumer.handlers.registration import handle_registration
from consumer.handlers.upload_file import upload_file_handler
from consumer.handlers.show_file import show_files
from consumer.handlers.profile_update import handle_profile_update
from consumer.handlers.profile import handle_profile_redis_update
from consumer.handlers.interaction import handle_like, handle_dislike
from consumer.logger import LOGGING_CONFIG, correlation_id_ctx, logger
from consumer.metrics import TOTAL_RECEIVED_MESSAGES
from consumer.schema.registration import RegistrationMessage
from consumer.schema.file import FileMessage
from consumer.schema.interaction import InteractionMessage
from consumer.storage import rabbit
from consumer.services.profile_service import load_and_store_matching_profiles
from consumer.storage.db import async_session


async def start_consumer() -> None:
    logging.config.dictConfig(LOGGING_CONFIG)
    logger.info('Starting consumer...')

    queue_name = 'user_messages'
    async with rabbit.channel_pool.acquire() as channel:
        # Will take no more than 10 messages in advance
        await channel.set_qos(prefetch_count=10)

        # Declaring exchange
        exchange = await channel.declare_exchange(
            'user_messages',
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )

        # Declaring queue
        queue = await channel.declare_queue(queue_name, durable=True)
        
        # Binding queue to exchange with routing key
        await queue.bind(exchange, routing_key='user_messages')
        
        logger.info('Consumer started and bound to exchange %s with routing key %s', exchange.name, 'user_messages')
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                TOTAL_RECEIVED_MESSAGES.inc()
                async with message.process():
                    # Set correlation_id if available, otherwise use a default
                    correlation_id = message.correlation_id or 'default_correlation_id'
                    correlation_id_ctx.set(correlation_id)

                    try:
                        # Try to unpack as InteractionMessage first
                        try:
                            body: InteractionMessage = InteractionMessage.model_validate(msgpack.unpackb(message.body))
                            logger.info('Interaction message received: %s', body)

                            if body.action == 'like':
                                await handle_like(body)
                                # Request new profiles after like
                                await handle_profile_redis_update({
                                    'user_id': body.user_id,
                                    'action': 'update_profile_redis',
                                    'request_type': 'like'
                                })
                            elif body.action == 'dislike':
                                await handle_dislike(body)
                                # Request new profiles after dislike
                                await handle_profile_redis_update({
                                    'user_id': body.user_id,
                                    'action': 'update_profile_redis',
                                    'request_type': 'dislike'
                                })
                            elif body.action == 'search':
                                # Handle search request
                                async with async_session() as db:
                                    # Get user preferences from profile
                                    from sqlalchemy import select
                                    from src.model.profile import Profile
                                    
                                    result = await db.execute(
                                        select(Profile).where(Profile.user_id == body.user_id)
                                    )
                                    profile = result.scalar_one_or_none()
                                    
                                    if profile:
                                        # Load and store matching profiles
                                        await load_and_store_matching_profiles(
                                            db=db,
                                            user_id=body.user_id,
                                            preferred_gender=profile.preferred_gender,
                                            preferred_age_min=profile.preferred_age_min,
                                            preferred_age_max=profile.preferred_age_max
                                        )
                                        logger.info('Matching profiles loaded for user %s', body.user_id)
                                    else:
                                        logger.warning('Profile not found for user %s', body.user_id)
                            else:
                                logger.warning('Unknown interaction action: %s', body.action)

                        except Exception:
                            # If not InteractionMessage, try as FileMessage
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

                                except Exception as e:
                                    logger.error('Failed to parse message: %s', e)
                                    continue

                    except Exception as e:
                        logger.error('Error processing message: %s', e)
                        continue
