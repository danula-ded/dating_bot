from aiogram.types import CallbackQuery, InputFile
from io import BytesIO

from config.settings import settings
from src.logger import logger
from src.storage.minio_client import download_file

from .router import router


@router.callback_query(lambda call: call.data.startswith('file:'))
async def handle_file_selection(callback: CallbackQuery) -> None:
    """
    Обрабатывает выбор файла из списка.
    Загружает файл из MinIO и отправляет его пользователю через Telegram.
    """
    if callback.data is None or callback.message is None:
        logger.error('Ошибка: callback не содержит данных.')
        return

    file_name = callback.data.split(':', 1)[1]
    user_id = callback.from_user.id

    try:
        # Download file from MinIO
        file_bytes = await download_file(file_name)
        if file_bytes is None:
            await callback.message.answer('Ошибка при загрузке файла.')
            return

        # Create InputFile from bytes
        input_file = InputFile(file_bytes, filename=file_name)
        
        # Send file to user
        await callback.message.answer_document(input_file)
        await callback.answer('Файл успешно отправлен!')
    except Exception as e:
        logger.error('Ошибка при отправке файла: %s', e)
        await callback.message.answer('Произошла ошибка при отправке файла.')
