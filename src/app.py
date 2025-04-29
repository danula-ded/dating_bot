import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from aio_pika import ExchangeType
from fastapi import FastAPI
from starlette_context import plugins
from starlette_context.middleware import RawContextMiddleware

from config.settings import settings
from src.api.minio.minio import router as minio_router
from src.api.tech.router import router
from src.api.tg.router import router as tg_router
from src.bg_tasks import background_tasks
from src.bot import bot, dp, setup_bot
from src.logger import LOGGING_CONFIG, logger
from src.routes.photo import router as photo_router
from src.storage.minio_client import create_bucket
from src.storage.rabbit import channel_pool


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logging.config.dictConfig(LOGGING_CONFIG)
    # Инициализируем MinIO bucket
    create_bucket()

    # Инициализируем общую очередь для передачи сообщений
    async with channel_pool.acquire() as channel:
        exchange = await channel.declare_exchange('user_files', ExchangeType.TOPIC, durable=True)

        users_queue = await channel.declare_queue(
            'user_messages',
            durable=True,
        )

        # Binding queue
        await users_queue.bind(exchange, 'user_messages')
    # #
    polling_task: asyncio.Task[None] | None = None
    wh_info = await bot.get_webhook_info()
    if settings.BOT_WEBHOOK_URL and wh_info.url != settings.BOT_WEBHOOK_URL:
        await bot.set_webhook(settings.BOT_WEBHOOK_URL)
    else:
        # Устанавливаем команды бота перед запуском
        await setup_bot()
        polling_task = asyncio.create_task(dp.start_polling(bot, handle_signals=False))

    logger.info('Finished start')
    yield

    if polling_task is not None:
        logger.info('Stopping polling...')
        polling_task.cancel()
        try:
            await polling_task
        except asyncio.CancelledError:
            logger.info('Polling stopped')

    while background_tasks:
        await asyncio.sleep(0)
    #
    await bot.delete_webhook()

    logger.info('Ending lifespan')


def create_app() -> FastAPI:
    app = FastAPI(docs_url='/swagger', lifespan=lifespan, title='Document Bot')
    app.include_router(router, prefix='', tags=['Metrics && Health'])
    app.include_router(tg_router, prefix='/tg', tags=['Telegram Webhook'])
    app.include_router(minio_router, prefix='/tg/webhook', tags=['MinIO API'])
    app.include_router(photo_router, prefix='/photo', tags=['Photo API'])

    app.add_middleware(RawContextMiddleware, plugins=[plugins.CorrelationIdPlugin()])
    return app


async def start_polling() -> None:
    logging.config.dictConfig(LOGGING_CONFIG)

    logger.info('Starting polling')

    await bot.delete_webhook()

    logging.error('Dependencies launched')
    await dp.start_polling(bot)


if __name__ == '__main__':
    uvicorn.run('src.app:create_app', factory=True, host='0.0.0.0', port=8000, workers=1)
