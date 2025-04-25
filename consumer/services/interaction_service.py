from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from consumer.logger import logger
from consumer.storage.redis import store_like
from src.model.user import User
from consumer.model.interaction import Like, Dislike
from consumer.model.rating import Rating


async def process_like(
    db: AsyncSession,
    user_id: int,
    target_user_id: int,
) -> bool:
    """
    Обрабатывает лайк от пользователя.

    Args:
        db: Сессия базы данных
        user_id: ID пользователя, который ставит лайк
        target_user_id: ID пользователя, которому ставят лайк

    Returns:
        bool: True если лайк успешно обработан, False в противном случае
    """
    try:
        # Проверяем, не лайкал ли уже этот пользователь
        existing_like = await db.execute(
            select(Like).where(and_(Like.user_id == user_id, Like.target_user_id == target_user_id))
        )
        if existing_like.scalar_one_or_none():
            logger.warning('User %s already liked user %s', user_id, target_user_id)
            return False

        # Создаем запись о лайке
        new_like = Like(user_id=user_id, target_user_id=target_user_id)
        db.add(new_like)

        # Обновляем activity_score в таблице рейтинга
        rating_result = await db.execute(select(Rating).where(Rating.user_id == target_user_id))
        rating = rating_result.scalar_one_or_none()
        if rating:
            # Увеличиваем activity_score на 0.5, но не больше 10
            rating.activity_score = min(rating.activity_score + 0.5, 10.0)

        # Сохраняем изменения в БД
        await db.commit()

        # Сохраняем информацию о лайке в Redis
        await store_like(user_id, target_user_id)

        logger.info('User %s liked user %s', user_id, target_user_id)
        return True

    except Exception as e:
        logger.error('Error processing like from user %s to user %s: %s', user_id, target_user_id, str(e))
        await db.rollback()
        return False


async def process_dislike(
    db: AsyncSession,
    user_id: int,
    target_user_id: int,
) -> bool:
    """
    Обрабатывает дизлайк от пользователя.

    Args:
        db: Сессия базы данных
        user_id: ID пользователя, который ставит дизлайк
        target_user_id: ID пользователя, которому ставят дизлайк

    Returns:
        bool: True если дизлайк успешно обработан, False в противном случае
    """
    try:
        # Проверяем, не дизлайкал ли уже этот пользователь
        existing_dislike = await db.execute(
            select(Dislike).where(and_(Dislike.user_id == user_id, Dislike.target_user_id == target_user_id))
        )
        if existing_dislike.scalar_one_or_none():
            logger.warning('User %s already disliked user %s', user_id, target_user_id)
            return False

        # Создаем запись о дизлайке
        new_dislike = Dislike(user_id=user_id, target_user_id=target_user_id)
        db.add(new_dislike)

        # Обновляем activity_score в таблице рейтинга
        rating_result = await db.execute(select(Rating).where(Rating.user_id == target_user_id))
        rating = rating_result.scalar_one_or_none()
        if rating:
            # Уменьшаем activity_score на 0.5, но не меньше 0
            rating.activity_score = max(rating.activity_score - 0.5, 0.0)

        # Сохраняем изменения в БД
        await db.commit()

        logger.info('User %s disliked user %s', user_id, target_user_id)
        return True

    except Exception as e:
        logger.error('Error processing dislike from user %s to user %s: %s', user_id, target_user_id, str(e))
        await db.rollback()
        return False
