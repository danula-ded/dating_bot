"""
Profile service for handling profile-related operations.
"""

from typing import Optional, Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.model.profile import Profile
from src.storage.db import get_db


async def get_profile_by_user_id(user_id: int) -> Optional[Profile]:
    """
    Get a profile by user ID.

    Args:
        user_id: The ID of the user whose profile to retrieve

    Returns:
        The profile if found, None otherwise
    """
    async for session in get_db():
        session: AsyncSession
        query = select(Profile).where(Profile.user_id == user_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()


async def update_profile(user_id: int, **kwargs: Any) -> Optional[Profile]:
    """
    Update a profile's information.

    Args:
        user_id: The ID of the user whose profile to update
        **kwargs: Fields to update with their new values

    Returns:
        The updated profile if found, None otherwise
    """
    async for session in get_db():
        session: AsyncSession
        # First check if profile exists
        profile = await get_profile_by_user_id(user_id)
        if not profile:
            return None

        # Update the profile
        stmt = update(Profile).where(Profile.user_id == user_id).values(**kwargs)
        await session.execute(stmt)
        await session.commit()

        # Return the updated profile
        return await get_profile_by_user_id(user_id)
