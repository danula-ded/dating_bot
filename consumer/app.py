import logging.config

import msgpack

from consumer.handlers.registration import handle_registration
from consumer.logger import LOGGING_CONFIG, correlation_id_ctx, logger
from consumer.metrics import TOTAL_RECEIVED_MESSAGES
from consumer.schema.registration import RegistrationMessage
from consumer.storage import rabbit


async def start_consumer() -> None:
    logging.config.dictConfig(LOGGING_CONFIG)
    logger.info('Starting consumer...')

    queue_name = 'user_registration_queue'
    async with rabbit.channel_pool.acquire() as channel:  # aio_pika.Channel

        # Will take no more than 10 messages in advance
        await channel.set_qos(prefetch_count=10)

        # Declaring queue
        queue = await channel.declare_queue(queue_name, durable=True)

        logger.info('Consumer started!')
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:  # aio_pika.Message
                TOTAL_RECEIVED_MESSAGES.inc()
                async with message.process():
                    if message.correlation_id is None:
                        logger.error('Message has no correlation_id')
                        return
                    correlation_id_ctx.set(message.correlation_id)

                    try:
                        body: RegistrationMessage = RegistrationMessage.model_validate(msgpack.unpackb(message.body))
                    logger.info('Message: %s', body)

                        if body.action == 'user_registration':
                            await handle_registration(body)
                    else:
                        logger.warning('Unknown action: %s', body.action)
                    except Exception as e:
                        logger.error('Error processing message: %s', e)
                        raise
