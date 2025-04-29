import json
from typing import List, Optional, Set

from redis import asyncio as aioredis
from consumer.logger import logger

# Redis connection pool
redis_pool = aioredis.ConnectionPool(
    host='redis', port=6379, db=0, decode_responses=True  # Using service name from docker-compose
)


async def get_redis() -> aioredis.Redis:
    """Get Redis connection from the pool."""
    return aioredis.Redis(connection_pool=redis_pool)


async def store_user_profiles(user_id: int, profiles: List[dict]) -> None:
    """
    Store user profiles in Redis as a list.

    Args:
        user_id: The ID of the user
        profiles: List of profile dictionaries to store
    """
    redis = await get_redis()
    key = f"user:{user_id}:profiles"

    try:
        # Clear existing profiles for this user
        await redis.delete(key)

        # Store each profile as a separate JSON string in the list
        for profile in profiles:
            await redis.rpush(key, json.dumps(profile))

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
        # Get all profiles from the list
        data = await redis.lrange(key, 0, -1)
        if data:
            # Parse each JSON string in the list
            profiles = [json.loads(profile) for profile in data]
            logger.info('Retrieved %d profiles for user %s from Redis', len(profiles), user_id)
            return profiles
        return None
    except Exception as e:
        logger.error('Error retrieving profiles from Redis for user %s: %s', user_id, e)
        raise


async def get_next_profile(user_id: int) -> Optional[dict]:
    """
    Get the next profile from the user's profile list.

    Args:
        user_id: The ID of the user

    Returns:
        The next profile dictionary or None if not found
    """
    redis = await get_redis()
    key = f"user:{user_id}:profiles"

    try:
        # Check if there are any profiles in the list
        profile_count = await redis.llen(key)
        if profile_count == 0:
            logger.info('No profiles for user %s in Redis', user_id)
            # Return a special indicator that there are no profiles
            return {"last_profile": True, "user_id": user_id, "no_profiles": True}

        # Get the first profile from the list
        data = await redis.lpop(key)
        if data:
            profile = json.loads(data)
            logger.info('Retrieved next profile for user %s from Redis', user_id)

            # Check if this was the last profile
            remaining_count = await redis.llen(key)
            if remaining_count == 0:
                logger.info('This was the last profile for user %s in Redis', user_id)
                # Add a flag to indicate this was the last profile
                profile["last_profile"] = True

            return profile

        return None
    except Exception as e:
        logger.error('Error retrieving next profile from Redis for user %s: %s', user_id, e)
        raise


async def store_like(user_id: int, target_user_id: int) -> None:
    """
    Store a like in Redis.

    Args:
        user_id: The ID of the user who gave the like
        target_user_id: The ID of the user who received the like
    """
    redis = await get_redis()
    key = f"user:{target_user_id}:likes"

    try:
        # Add user_id to the set of users who liked target_user_id
        await redis.sadd(key, user_id)
        logger.info('Stored like from user %s to user %s in Redis', user_id, target_user_id)
    except Exception as e:
        logger.error('Error storing like in Redis: %s', e)
        raise


async def get_likes(user_id: int) -> Set[str]:
    """
    Get all users that have liked a user from Redis.

    Args:
        user_id: The ID of the user

    Returns:
        Set of user IDs that have liked the user
    """
    redis = await get_redis()
    key = f"user:{user_id}:likes"

    try:
        # Get all members of the set
        likes = await redis.smembers(key)
        logger.info('Retrieved %d likes for user %s from Redis', len(likes), user_id)
        return likes
    except Exception as e:
        logger.error('Error retrieving likes from Redis for user %s: %s', user_id, e)
        raise
