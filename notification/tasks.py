"""Celery tasks for notification service."""
from typing import Dict, List, Any
import asyncio
import aiohttp
import tempfile
import os

from redis import asyncio as aioredis
from sqlalchemy import select, join
from notification.logger import logger
from minio import Minio

from notification.bot import bot
from notification.storage.db import async_session
from notification.storage.models import User, Profile, City
from notification.celery_app import celery_app
from config.settings import settings

# Initialize Minio client
minio_client = Minio(
    settings.MINIO_URL.replace('http://', '').replace('https://', ''),
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_URL.startswith('https')
)

# Log startup message
logger.info('Notification service started. Checking for likes every 2 minutes.')

# Redis connection pool
redis_pool = aioredis.ConnectionPool(
    host='redis',
    port=6379,
    db=0,
    decode_responses=True,
    max_connections=10
)


async def get_redis() -> aioredis.Redis:
    """Get Redis connection from the pool."""
    return aioredis.Redis(connection_pool=redis_pool)


async def get_likes_for_user(user_id: int) -> List[int]:
    """Get all likes for a specific user from Redis."""
    redis = await get_redis()
    key = f'user:{user_id}:likes'
    
    try:
        likes: set[str] = await redis.smembers(key)  # type: ignore
        logger.info('Found %d likes for user %s', len(likes), user_id)
        return [int(like) for like in likes]
    except Exception as e:
        logger.error('Error getting likes for user %s: %s', user_id, str(e))
        return []
    finally:
        await redis.close()


async def download_from_presigned_url(url: str) -> str | None:
    """Download file from presigned URL and return local path."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    content = await resp.read()
                    # Create a temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as f:
                        f.write(content)
                        return f.name
    except Exception as e:
        logger.error('Error downloading file from URL: %s', e)
        return None


async def get_user_info(user_id: int) -> Dict[str, Any]:
    """Get user information from PostgreSQL by user_id."""
    async with async_session() as session:
        try:
            # Join users with profile and city tables to get all user info
            query = select(
                User.username,
                User.first_name,
                User.gender,
                User.age,
                Profile.bio,
                City.name.label('city'),
                Profile.photo_url
            ).select_from(
                join(User, Profile, User.user_id == Profile.user_id)
                .join(City, User.city_id == City.city_id)
            ).where(User.user_id == user_id)

            result = await session.execute(query)
            user = result.first()
            
            if user:
                return {
                    'username': user.username,
                    'first_name': user.first_name,
                    'gender': user.gender,
                    'age': user.age,
                    'bio': user.bio,
                    'city': user.city,
                    'photo_url': user.photo_url
                }
            logger.error('User not found in database: %s', user_id)
            return {}
        except Exception as e:
            logger.error('Error getting user info for user %s: %s', user_id, str(e))
            return {}


async def send_notification(user_id: int, likes: List[int]) -> None:
    """Send notification to user about new likes."""
    redis = await get_redis()
    key = f'user:{user_id}:likes'
    
    try:
        if not likes:
            logger.info('No likes to process for user %s', user_id)
            return
            
        for from_user_id in likes:
            user_info = await get_user_info(from_user_id)
            
            if not user_info:
                logger.warning('User info not found for like from user %s', from_user_id)
                continue
                
            message = (
                f'👤 Профиль пользователя:\n\n'
                f'Имя: {user_info["first_name"]}\n'
                f'Пол: {user_info["gender"]}\n'
                f'Возраст: {user_info["age"]}\n'
                f'Город: {user_info["city"]}\n'
                f'О себе: {user_info["bio"]}\n'
                f'Username: @{user_info["username"]}\n\n'
            )
            
            if user_info.get('photo_url'):
                try:
                    # Download the photo from the presigned URL
                    local_path = await download_from_presigned_url(user_info['photo_url'])
                    if local_path:
                        # Send photo with caption
                        await bot.send_photo(
                            chat_id=user_id,
                            photo=local_path,
                            caption=message
                        )
                        
                        # Clean up the temporary file
                        try:
                            os.unlink(local_path)
                        except Exception as e:
                            logger.error('Error deleting temporary file: %s', e)
                    else:
                        logger.error('Failed to download photo for user %s', from_user_id)
                        await bot.send_message(
                            chat_id=user_id,
                            text=message
                        )
                except Exception as e:
                    logger.error('Error sending photo for user %s: %s', from_user_id, str(e))
                    await bot.send_message(
                        chat_id=user_id,
                        text=message
                    )
            else:
                await bot.send_message(
                    chat_id=user_id,
                    text=message
                )
            
            logger.info('Notification sent to user %s about like from %s', user_id, from_user_id)
            await redis.srem(key, str(from_user_id))  # type: ignore
            logger.info('Removed processed like from user %s', from_user_id)
        
    except Exception as e:
        logger.error('Error sending notification to user %s: %s', user_id, str(e))
    finally:
        await redis.close()


@celery_app.task(name='notification.tasks.check_likes', bind=True)
def check_likes(self) -> None:
    """Check for new likes and send notifications."""
    logger.info('Starting check_likes task')
    
    async def _check_likes() -> None:
        redis = await get_redis()
        try:
            user_keys = await redis.keys('user:*:likes')
            logger.info('Found %d users with likes', len(user_keys))
            
            for key in user_keys:
                user_id = int(key.split(':')[1])
                logger.info('Processing likes for user %s', user_id)
                
                likes = await get_likes_for_user(user_id)
                if likes:
                    await send_notification(user_id, likes)
                    
        except Exception as e:
            logger.error('Error in check_likes task: %s', str(e))
            raise
        finally:
            await redis.close() 
    
    # Run the async function in an event loop
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_check_likes())
    logger.info('Completed check_likes task')