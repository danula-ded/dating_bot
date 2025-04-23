from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from config.settings import settings
from src.handlers.callback.router import router as callback_router
from src.handlers.command.router import router as command_router
from src.handlers.message.router import router as message_router
from src.storage.redis_client import redis_storage

dp = Dispatcher(storage=RedisStorage(redis=redis_storage))
default = DefaultBotProperties(parse_mode=ParseMode.HTML)
bot = Bot(token=settings.BOT_TOKEN, default=default)

# Регистрируем роутеры в правильном порядке
# Сначала команды, потом сообщения, потом колбэки
dp.include_router(command_router)  # Обработка команд (/start, /help и т.д.)
dp.include_router(message_router)  # Обработка сообщений (регистрация, файлы и т.д.)
dp.include_router(callback_router)  # Обработка колбэков (кнопки и т.д.)
