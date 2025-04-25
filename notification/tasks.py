"""Celery tasks for notification service."""
import json
from typing import Dict, List

from celery import shared_task
from redis import asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.logger import logger

from consumer.bot import bot
from consumer.storage.db import async_session
from consumer.storage.models import User

# Redis connection pool
redis_pool = aioredis.ConnectionPool(
    host='redis',
    port=6379,
    db=0,
    decode_responses=True
)

async def get_redis() -> aioredis.Redis:
    """Get Redis connection from the pool."""
    return aioredis.Redis(connection_pool=redis_pool)

async def get_likes_for_user(user_id: int) -> List[Dict]:
    """
    Get all likes for a specific user from Redis.
    
    Args:
        user_id: The ID of the user
        
    Returns:
        List of like events
    """
    redis = await get_redis()
    key = f"user:{user_id}:likes"
    
    try:
        likes = await redis.lrange(key, 0, -1)
        return [json.loads(like) for like in likes]
    except Exception as e:
        logger.error('Error getting likes for user %s: %s', user_id, str(e))
        return []

async def get_username_by_id(user_id: int) -> str:
    """
    Get username from PostgreSQL by user_id.
    
    Args:
        user_id: The ID of the user
        
    Returns:
        Username of the user
    """
    async with async_session() as session:
        try:
            result = await session.execute(
                select(User.username).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if user:
                return user
            logger.error('User not found in database: %s', user_id)
            return ''
        except Exception as e:
            logger.error('Error getting username for user %s: %s', user_id, str(e))
            return ''

async def send_notification(user_id: int, like_data: Dict) -> None:
    """
    Send notification to user about new like.
    
    Args:
        user_id: The ID of the user to notify
        like_data: The like event data
    """
    try:
        # Get username of the user who liked
        from_username = await get_username_by_id(like_data['from_user_id'])
        if not from_username:
            logger.error('Could not send notification: from_username not found')
            return
            
        # Send notification through bot
        message = (
            f'❤️ Новый лайк!\n\n'
            f'Пользователь @{from_username} поставил вам лайк.\n'
            f'Рейтинг: {like_data.get("rating", "не указан")}'
        )
        
        await bot.send_message(
            chat_id=user_id,
            text=message
        )
        logger.info('Notification sent to user %s about like from %s', 
                    user_id, like_data['from_user_id'])
    except Exception as e:
        logger.error('Error sending notification to user %s: %s', user_id, str(e))

@shared_task
async def check_likes() -> None:
    """Check for new likes and send notifications."""
    redis = await get_redis()
    
    try:
        # Get all users who have likes
        user_keys = await redis.keys('user:*:likes')
        
        for key in user_keys:
            # Extract user_id from key
            user_id = int(key.split(':')[1])
            
            # Get likes for user
            likes = await get_likes_for_user(user_id)
            
            for like in likes:
                # Send notification for each like
                await send_notification(user_id, like)
                
                # Remove processed like from Redis
                await redis.lrem(key, 1, json.dumps(like))
                
    except Exception as e:
        logger.error('Error in check_likes task: %s', str(e)) 