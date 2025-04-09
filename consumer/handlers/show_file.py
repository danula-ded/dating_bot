from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.future import select

from consumer.bot import bot
from consumer.logger import logger  # Импорт логгера
from consumer.schema.file import FileMessage
from consumer.storage import db
from src.model.file import FileRecord


async def show_files(message: FileMessage) -> None:
    """Обработчик действия show_files_user."""
    if not message:
        logger.error('Message is not an instance of FileMessage: %s', message)
        return

    user_id = message.user_id

    logger.info('User ID: %s', user_id)

    # Получение списка файлов из базы данных
    async with db.async_session() as session:
        result = await session.execute(select(FileRecord.file_name).where(FileRecord.user_id == user_id))
        files = result.scalars().all()

    logger.info('Files for user %s: %s', user_id, files)

    # Отправка сообщения через Telegram-бота
    if not files:
        await bot.send_message(chat_id=user_id, text='У вас нет загруженных файлов.')
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=file, callback_data=f'file:{file}')] for file in files]
    )

    await bot.send_message(chat_id=user_id, text='Ваши файлы:', reply_markup=keyboard)
