"""
City service for handling city-related operations.
"""

from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.model.city import City
from src.storage.db import get_db


async def get_city_by_id(city_id: int) -> Optional[City]:
    """
    Get a city by its ID.

    Args:
        city_id: The ID of the city to retrieve

    Returns:
        The city if found, None otherwise
    """
    async with get_db() as session:
        session: AsyncSession
        query = select(City).where(City.city_id == city_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()


async def search_cities(query: str) -> List[City]:
    """
    Search for cities by name.

    Args:
        query: The search query string

    Returns:
        List of matching cities
    """
    async with get_db() as session:
        session: AsyncSession
        search_query = select(City).where(City.name.ilike(f"%{query}%"))
        result = await session.execute(search_query)
        return list(result.scalars().all())
