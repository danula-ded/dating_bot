from minio import Minio
from minio.error import S3Error
import os
from typing import Optional

# MinIO configuration
MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'minio:9000')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
MINIO_SECURE = os.getenv('MINIO_SECURE', 'false').lower() == 'true'
MINIO_BUCKET = os.getenv('MINIO_BUCKET', 'dating-app')

# Initialize MinIO client
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE
)

async def check_minio_connection() -> bool:
    """
    Check if MinIO connection is working by attempting to list buckets.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        minio_client.list_buckets()
        return True
    except S3Error as e:
        print(f"MinIO connection error: {e}")
        return False

def ensure_bucket_exists(bucket_name: str = MINIO_BUCKET) -> None:
    """
    Ensure that the specified bucket exists in MinIO.
    If it doesn't exist, create it.
    
    Args:
        bucket_name (str): Name of the bucket to check/create
    """
    try:
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
            print(f"Created bucket: {bucket_name}")
    except S3Error as e:
        print(f"Error ensuring bucket exists: {e}")
        raise

# Ensure the default bucket exists on startup
ensure_bucket_exists() 