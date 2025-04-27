"""
User service for handling user-related operations.
"""

from typing import Optional, Dict, Any

from sqlalchemy import select, update

from src.model.user import User
from src.storage.db import async_session


async def get_user_by_id(user_id: int) -> Optional[User]:  # noqa
    """
    Get a user by their ID.

    Args:
        user_id: The ID of the user to retrieve

    Returns:
        The user if found, None otherwise
    """
    async with async_session() as session:
        query = select(User).where(User.user_id == user_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()


async def update_user(user_id: int, **kwargs: Any) -> Optional[User]:
    """
    Update a user's information.

    Args:
        user_id: The ID of the user to update
        **kwargs: Fields to update with their new values

    Returns:
        The updated user if found, None otherwise
    """
    async with async_session() as session:
        # First check if user exists
        user = await get_user_by_id(user_id)
        if not user:
            return None

        # Update the user
        stmt = update(User).where(User.user_id == user_id).values(**kwargs)
        await session.execute(stmt)
        await session.commit()

        # Return the updated user
        return await get_user_by_id(user_id)
