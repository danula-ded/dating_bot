from pathlib import Path

from sqlalchemy import select

from config.settings import settings
from consumer.logger import logger
from consumer.schema.file import FileMessage
from src.model.file import FileRecord
from src.storage.db import async_session
from src.storage.minio_client import check_minio_connection, minio_client


async def upload_file_handler(body: FileMessage) -> None:
    """Обрабатывает сообщение от RabbitMQ и сохраняет запись в PostgreSQL."""

    try:
        user_id = body.user_id
        file_name = body.file_name

        if file_name is None:
            logger.error('file_name не может быть None.')
            return

        # Проверяем соединение с MinIO
        if not check_minio_connection():
            logger.error('Нет соединения с MinIO')
            return

        # Формируем полный путь к файлу
        file_path = f'{user_id}_{file_name}'  # Используем тот же формат, что и в боте

        # Проверяем существование файла в MinIO
        try:
            minio_client.stat_object(settings.MINIO_BUCKET_NAME, file_path)
        except Exception as e:
            logger.error('Файл %s не найден в MinIO: %s', file_path, e)
            return

        # Сохраняем запись в БД
        async with async_session() as db:
            # Проверяем, не существует ли уже запись
            existing_record = await db.execute(
                select(FileRecord).where(
                    FileRecord.user_id == user_id,
                    FileRecord.file_name == file_name
                )
            )
            if existing_record.scalar_one_or_none():
                logger.warning('Файл %s уже существует в БД для пользователя %s', file_name, user_id)
                return

            record = FileRecord(
                user_id=user_id,
                file_name=file_name,
                file_exention=Path(file_name).suffix,
                file_path=file_path,
            )
            db.add(record)
            await db.commit()

        logger.info('Запись для файла %s успешно добавлена в БД для пользователя %s', file_name, user_id)
    except Exception as e:
        logger.error('Ошибка при обработке файла в консюмере: %s', e)
        # Откатываем транзакцию в случае ошибки
        async with async_session() as db:
            await db.rollback()
