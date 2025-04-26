"""
Profile service for handling profile-related operations.
"""

from typing import Optional

from sqlalchemy import select
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
