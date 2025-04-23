from redis.asyncio import ConnectionPool, Redis

from config.settings import settings

# Настройка пула подключений
pool = ConnectionPool(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
redis_storage = Redis(connection_pool=pool)


async def set_user_state(user_id: int, state: str) -> None:
    """Сохранение состояния пользователя."""
    await redis_storage.set(f'user:{user_id}:state', state, ex=600)


async def get_user_state(user_id: int) -> str | None:
    """Получение состояния пользователя."""
    return await redis_storage.get(f'user:{user_id}:state')


async def clear_user_state(user_id: int) -> None:
    """Удаление состояния пользователя."""
    await redis_storage.delete(f'user:{user_id}:state')
