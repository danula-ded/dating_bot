from io import BytesIO

from minio import Minio

MINIO_URL = 'http://localhost:9000'
MINIO_ACCESS_KEY = 'minioadmin'
MINIO_SECRET_KEY = 'minioadmin'
MINIO_BUCKET_NAME = 'test-bucket'

minio_client = Minio(
    MINIO_URL.replace('http://', '').replace('https://', ''),
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False,
)


def create_bucket() -> None:
    if not minio_client.bucket_exists(MINIO_BUCKET_NAME):
        minio_client.make_bucket(MINIO_BUCKET_NAME)
        print(f'Bucket {MINIO_BUCKET_NAME} создан.')
    else:
        print(f'Bucket {MINIO_BUCKET_NAME} уже существует.')


def upload_file(user_id: int, file_name: str, file_data: bytes) -> str:
    unique_name = f'{user_id}_{file_name}'
    minio_client.put_object(
        MINIO_BUCKET_NAME,
        unique_name,
        BytesIO(file_data),
        length=len(file_data),
    )
    print(f'Файл {unique_name} загружен.')
    return unique_name


def get_file_path(file_name: str) -> str:
    url = minio_client.presigned_get_object(MINIO_BUCKET_NAME, file_name)
    print(f'URL файла: {url}')
    return url


if __name__ == '__main__':
    create_bucket()
    file_name = upload_file(123, 'example.txt', b'Hello, MinIO!')
    get_file_path(file_name)
