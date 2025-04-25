"""
User service for handling user-related operations.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.model.user import User
from src.storage.db import get_db


async def get_user_by_id(user_id: int) -> Optional[User]:
    """
    Get a user by their ID.

    Args:
        user_id: The ID of the user to retrieve

    Returns:
        The user if found, None otherwise
    """
    async with get_db() as session:
        session: AsyncSession
        query = select(User).where(User.user_id == user_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()
