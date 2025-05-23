from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BOT_TOKEN: str
    BOT_WEBHOOK_URL: str

    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    RABBIT_HOST: str  # = 'localhost' # rabbitmq
    RABBIT_PORT: int  # = 5672
    RABBIT_USER: str  # = 'guest'
    RABBIT_PASSWORD: str  # = 'guest'

    REDIS_HOST: str
    REDIS_PORT: str

    # Добавляем MinIO настройки
    MINIO_URL: str  # = 'http://localhost:9000'
    MINIO_ACCESS_KEY: str  # = 'minioadmin'
    MINIO_SECRET_KEY: str  # = 'minioadmin'
    MINIO_BUCKET_NAME: str  # = 'documents'

    @property
    def db_url(self) -> str:
        return f'postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'

    @property
    def rabbit_url(self) -> str:
        return f'amqp://{self.RABBIT_USER}:{self.RABBIT_PASSWORD}@{self.RABBIT_HOST}:{self.RABBIT_PORT}/'

    class Config:
        env_file = 'config/.env'


settings = Settings()
