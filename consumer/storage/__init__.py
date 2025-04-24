from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from consumer.storage.db import get_db


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Контекстный менеджер для получения сессии базы данных.
    
    Yields:
        AsyncSession: Сессия базы данных
    """
    async for session in get_db():
        yield session
