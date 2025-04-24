from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from consumer.logger import logger
from consumer.storage.redis import store_like, get_likes
from src.model.user import User
from consumer.model.interaction import Like, Dislike


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
            select(Like).where(
                and_(
                    Like.user_id == user_id,
                    Like.target_user_id == target_user_id
                )
            )
        )
        if existing_like.scalar_one_or_none():
            logger.warning(
                'User %s already liked user %s',
                user_id,
                target_user_id
            )
            return False

        # Создаем запись о лайке
        new_like = Like(
            user_id=user_id,
            target_user_id=target_user_id
        )
        db.add(new_like)

        # Обновляем active_score для пользователя, которому поставили лайк
        target_user = await db.execute(
            select(User).where(User.user_id == target_user_id)
        )
        target_user = target_user.scalar_one_or_none()
        if target_user:
            # Увеличиваем active_score на 1, но не больше 5
            target_user.active_score = min(target_user.active_score + 1, 5)

        # Сохраняем изменения в БД
        await db.commit()

        # Сохраняем информацию о лайке в Redis
        await store_like(user_id, target_user_id)

        logger.info(
            'User %s liked user %s',
            user_id,
            target_user_id
        )
        return True

    except Exception as e:
        logger.error(
            'Error processing like from user %s to user %s: %s',
            user_id,
            target_user_id,
            str(e)
        )
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
            select(Dislike).where(
                and_(
                    Dislike.user_id == user_id,
                    Dislike.target_user_id == target_user_id
                )
            )
        )
        if existing_dislike.scalar_one_or_none():
            logger.warning(
                'User %s already disliked user %s',
                user_id,
                target_user_id
            )
            return False

        # Создаем запись о дизлайке
        new_dislike = Dislike(
            user_id=user_id,
            target_user_id=target_user_id
        )
        db.add(new_dislike)

        # Обновляем active_score для пользователя, которому поставили дизлайк
        target_user = await db.execute(
            select(User).where(User.user_id == target_user_id)
        )
        target_user = target_user.scalar_one_or_none()
        if target_user:
            # Уменьшаем active_score на 1, но не меньше 0
            target_user.active_score = max(target_user.active_score - 1, 0)

        # Сохраняем изменения в БД
        await db.commit()

        logger.info(
            'User %s disliked user %s',
            user_id,
            target_user_id
        )
        return True

    except Exception as e:
        logger.error(
            'Error processing dislike from user %s to user %s: %s',
            user_id,
            target_user_id,
            str(e)
        )
        await db.rollback()
        return False 