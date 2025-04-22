from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.future import select

from config.settings import settings
from consumer.bot import bot
from consumer.logger import logger  # Импорт логгера
from consumer.schema.file import FileMessage
from consumer.storage import db
from src.model.file import FileRecord
from src.storage.minio_client import check_minio_connection, minio_client


async def show_files(message: FileMessage) -> None:
    """Обработчик действия show_files_user."""
    if not message:
        logger.error('Message is not an instance of FileMessage: %s', message)
        return

    user_id = message.user_id

    logger.info('User ID: %s', user_id)

    # Проверяем соединение с MinIO
    if not check_minio_connection():
        await bot.send_message(chat_id=user_id, text='Ошибка: сервис хранения файлов недоступен.')
        return

    # Получение списка файлов из базы данных
    async with db.async_session() as session:
        result = await session.execute(select(FileRecord).where(FileRecord.user_id == user_id))
        files = result.scalars().all()

    logger.info('Files for user %s: %s', user_id, files)

    # Отправка сообщения через Telegram-бота
    if not files:
        await bot.send_message(chat_id=user_id, text='У вас нет загруженных файлов.')
        return

    # Проверяем существование каждого файла в MinIO
    valid_files = []
    for file in files:
        try:
            # Проверяем существование файла в MinIO
            minio_client.stat_object(settings.MINIO_BUCKET_NAME, file.file_path)
            valid_files.append(file)
        except Exception as e:
            logger.error('Файл %s не найден в MinIO: %s', file.file_path, e)
            # Можно добавить удаление записи из БД, если файл не найден
            continue

    if not valid_files:
        await bot.send_message(chat_id=user_id, text='У вас нет доступных файлов.')
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=file.file_name, callback_data=f'file:{file.file_path}')] for file in valid_files
        ]
    )

    await bot.send_message(chat_id=user_id, text='Ваши файлы:', reply_markup=keyboard)
