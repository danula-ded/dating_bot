from sqlalchemy import select

from consumer.logger import logger
from consumer.storage.db import async_session
from consumer.services.profile_service import load_and_store_matching_profiles
from src.model.user import User


async def handle_profile_redis_update(message: dict) -> None:
    """
    Обрабатывает запрос на обновление профилей в Redis.

    Args:
        message: Сообщение из очереди с данными:
            - user_id: ID пользователя
            - action: 'update_profile_redis'
            - request_type: тип запроса ('search', 'like', 'dislike')
    """
    try:
        user_id = message['user_id']

        async with async_session() as db:
            # Получаем пользователя для определения его предпочтений
            result = await db.execute(select(User).where(User.user_id == user_id))
            user = result.scalar_one_or_none()

            if not user:
                logger.error('User %s not found', user_id)
                return

            # Загружаем и сохраняем подходящие профили
            await load_and_store_matching_profiles(
                db=db,
                user_id=user_id,
                preferred_gender=user.preferred_gender,
                preferred_age_min=user.preferred_age_min,
                preferred_age_max=user.preferred_age_max,
            )

    except Exception as e:
        logger.error('Error updating Redis profiles: %s', e)
        raise
