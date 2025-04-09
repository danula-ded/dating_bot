import logging.config

import msgpack

from consumer.handlers.show_file import show_files
from consumer.handlers.upload_file import upload_file_handler
from consumer.logger import LOGGING_CONFIG, correlation_id_ctx, logger
from consumer.metrics import TOTAL_RECEIVED_MESSAGES
from consumer.schema.file import FileMessage
from consumer.storage import rabbit


async def start_consumer() -> None:
    logging.config.dictConfig(LOGGING_CONFIG)
    logger.info('Starting consumer...')

    queue_name = 'user_messages'
    async with rabbit.channel_pool.acquire() as channel:  # aio_pika.Channel

        # Will take no more than 10 messages in advance
        await channel.set_qos(prefetch_count=10)  # TODO почитать

        # Declaring queue
        queue = await channel.declare_queue(queue_name, durable=True)

        logger.info('Consumer started!')
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:  # aio_pika.Message
                TOTAL_RECEIVED_MESSAGES.inc()
                async with message.process():
                    if message.correlation_id is None:
                        logger.error('Message has no correlation_id')
                        return  # после выхода из with будет ack (есть еще no_ack)
                    correlation_id_ctx.set(message.correlation_id)

                    body: FileMessage = FileMessage.model_validate(msgpack.unpackb(message.body))
                    logger.info('Message: %s', body)

                    if body.action == 'show_files_user':
                        await show_files(body)
                    elif body.action == 'upload_file':
                        await upload_file_handler(body)
                    else:
                        logger.warning('Unknown action: %s', body.action)
