from fastapi import HTTPException, Query
from fastapi.responses import StreamingResponse  # , FileResponse

from src.logger import logger
from src.storage.minio_client import download_file

from .router import router


@router.get('/get-file', summary='Скачать файл')
async def get_file(
    user_id: int = Query(..., description='ID пользователя'), file_name: str = Query(..., description='Имя файла')
) -> StreamingResponse:
    """
    Скачивает файл из MinIO и возвращает его в виде потока байтов.

    Args:
        user_id (int): ID пользователя.
        file_name (str): Имя файла.

    Returns:
        StreamingResponse: Файл в виде потока байтов.
    """

    # Используем file_name как есть, так как он уже содержит user_id
    minio_path = file_name

    # Скачиваем файл из MinIO
    try:
        # Загружаем файл в байтах
        file_bytes = await download_file(minio_path)
        logger.info('Файл %s скачан из MinIO.', file_name)
    except Exception as e:
        logger.error('Ошибка при скачивании файла: %s', e)
        raise HTTPException(status_code=500, detail='Ошибка при скачивании файла.')

    # Возвращаем файл пользователю
    return StreamingResponse(
        file_bytes,
        media_type='application/octet-stream',
        headers={'Content-Disposition': f'attachment; filename={file_name}'},
    )
