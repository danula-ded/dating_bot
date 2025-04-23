import json
from typing import List, Optional

from redis import asyncio as aioredis
from consumer.logger import logger

# Redis connection pool
redis_pool = aioredis.ConnectionPool(
    host='redis',  # Using service name from docker-compose
    port=6379,
    db=0,
    decode_responses=True
)

async def get_redis() -> aioredis.Redis:
    """Get Redis connection from the pool."""
    return aioredis.Redis(connection_pool=redis_pool)

async def store_user_profiles(user_id: int, profiles: List[dict]) -> None:
    """
    Store user profiles in Redis.
    
    Args:
        user_id: The ID of the user
        profiles: List of profile dictionaries to store
    """
    redis = await get_redis()
    key = f"user:{user_id}:profiles"
    
    try:
        # Store profiles as JSON string
        await redis.set(key, json.dumps(profiles))
        logger.info('Stored %d profiles for user %s in Redis', len(profiles), user_id)
    except Exception as e:
        logger.error('Error storing profiles in Redis for user %s: %s', user_id, e)
        raise

async def get_user_profiles(user_id: int) -> Optional[List[dict]]:
    """
    Get user profiles from Redis.
    
    Args:
        user_id: The ID of the user
        
    Returns:
        List of profile dictionaries or None if not found
    """
    redis = await get_redis()
    key = f"user:{user_id}:profiles"
    
    try:
        data = await redis.get(key)
        if data:
            profiles = json.loads(data)
            logger.info('Retrieved %d profiles for user %s from Redis', len(profiles), user_id)
            return profiles
        return None
    except Exception as e:
        logger.error('Error retrieving profiles from Redis for user %s: %s', user_id, e)
        raise 