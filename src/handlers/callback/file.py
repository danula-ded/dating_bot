from aiogram.types import CallbackQuery, URLInputFile

from config.settings import settings
from src.logger import logger

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

    # URL ручки FastAPI для скачивания файла
    api_url = f'{settings.BOT_WEBHOOK_URL}/get-file'

    try:
        await callback.message.answer_document(
            URLInputFile(api_url + f'?user_id={user_id}&file_name={file_name}', filename=file_name)
        )
        await callback.answer('Файл успешно отправлен!')
    except Exception as e:
        logger.error('Ошибка при отправке файла: %s', e)
        await callback.message.answer('Произошла ошибка при отправке файла.')
