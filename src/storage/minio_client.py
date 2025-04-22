import io
from io import BytesIO

from minio import Minio

from config.settings import settings
from src.logger import logger

# Инициализация Minio клиента
minio_client = Minio(
    settings.MINIO_URL.replace('http://', '').replace('https://', ''),
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=False,
)


def create_bucket() -> None:
    """Создает бакет, если он не существует."""
    if not minio_client.bucket_exists(settings.MINIO_BUCKET_NAME):
        minio_client.make_bucket(settings.MINIO_BUCKET_NAME)


def upload_file(user_id: int, file_name: str, file_data: bytes) -> str:
    """
    Загружает файл в MinIO.

    Args:
        user_id (int): ID пользователя.
        file_name (str): Имя файла.
        file_data (bytes): Данные файла.

    Returns:
        str: Уникальное имя файла в бакете.
    """
    unique_name = f'{user_id}_{file_name}'
    # Оборачиваем данные в BytesIO
    file_stream = BytesIO(file_data)
    minio_client.put_object(
        bucket_name=settings.MINIO_BUCKET_NAME,
        object_name=unique_name,
        data=file_stream,
        length=len(file_data),
        content_type='application/octet-stream',
    )
    return unique_name


def get_file_path(file_name: str) -> str:
    """
    Возвращает временный URL для доступа к файлу.

    Args:
        file_name (str): Имя файла в бакете.

    Returns:
        str: Подписанный URL для доступа к файлу.
    """
    return minio_client.presigned_get_object(settings.MINIO_BUCKET_NAME, file_name)


async def download_file(minio_path: str) -> io.BytesIO:
    """
    Скачивает файл из MinIO и возвращает его в виде объекта BytesIO.

    Args:
        minio_path (str): Путь к файлу в MinIO.

    Returns:
        io.BytesIO: Содержимое файла.
    """
    try:
        # Получаем объект из MinIO
        response = minio_client.get_object(settings.MINIO_BUCKET_NAME, minio_path)

        # Читаем содержимое в BytesIO
        file_bytes = io.BytesIO(response.read())
        file_bytes.seek(0)

        # Освобождаем ресурсы MinIO
        response.close()
        response.release_conn()

        return file_bytes
    except Exception as e:
        logger.error('Ошибка при загрузке файла {minio_path} из MinIO: %s', e)
        raise


def check_minio_connection() -> bool:
    """Проверяет соединение с MinIO"""
    try:
        # Пробуем получить список бакетов
        minio_client.list_buckets()
        return True
    except Exception as e:
        logger.error('Ошибка подключения к MinIO: %s', e)
        return False
