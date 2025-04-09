from pathlib import Path

from consumer.logger import logger
from consumer.schema.file import FileMessage
from src.model.file import FileRecord
from src.storage.db import async_session


async def upload_file_handler(body: FileMessage) -> None:
    """Обрабатывает сообщение от RabbitMQ и сохраняет запись в PostgreSQL."""

    try:
        user_id = body.user_id
        file_name = body.file_name

        if file_name is None:
            logger.error('file_name не может быть None.')
            return

        file_path = f'{user_id}_{file_name}'

        # Сохраняем запись в БД
        async with async_session() as db:
            record = FileRecord(
                user_id=user_id,
                file_name=file_name,
                file_exention=Path(file_name).suffix,
                file_path=file_path,  # Полученный путь
            )
            db.add(record)
            await db.commit()

        logger.info('Запись для файла %s успешно добавлена в БД для пользователя %s.', file_name, user_id)
    except Exception as e:
        logger.error('Ошибка при обработке файла в консюмере: %s', e)
