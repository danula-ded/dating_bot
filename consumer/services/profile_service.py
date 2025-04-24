from sqlalchemy import select, func, and_, case, desc
from sqlalchemy.ext.asyncio import AsyncSession

from consumer.logger import logger
from consumer.storage.redis import store_user_profiles
from consumer.model.interaction import Like, Dislike
from src.model.profile import Profile
from src.model.user import User


async def load_and_store_matching_profiles(
    db: AsyncSession,
    user_id: int,
    preferred_gender: str | None = None,
    preferred_age_min: int | None = None,
    preferred_age_max: int | None = None,
    limit: int = 5,
) -> list:
    """
    Загружает подходящие профили и сохраняет их в Redis.
    
    Args:
        db: Сессия базы данных
        user_id: ID пользователя, для которого ищем профили
        preferred_gender: Предпочтительный пол (опционально)
        preferred_age_min: Минимальный предпочтительный возраст (опционально)
        preferred_age_max: Максимальный предпочтительный возраст (опционально)
        limit: Количество профилей для загрузки
        
    Returns:
        list: Список загруженных профилей
    """
    # Получаем пользователя для определения его города
    user_result = await db.execute(select(User).where(User.user_id == user_id))
    user = user_result.scalar_one_or_none()
    
    if not user:
        logger.error('User %s not found', user_id)
        return []
    
    # Базовый запрос для получения всех подходящих профилей
    query = (
        select(
            Profile,
            User,
            # Базовый счетчик активности (количество лайков и дизлайков)
            func.count(Like.id).label('likes_count'),
            func.count(Dislike.id).label('dislikes_count'),
            # Счетчик общего скора
            (func.count(Like.id) + func.count(Dislike.id)).label('activity_score'),
        )
        .join(User, Profile.user_id == User.user_id)
        .outerjoin(Like, User.user_id == Like.target_user_id)
        .outerjoin(Dislike, User.user_id == Dislike.target_user_id)
        .where(
            and_(
                Profile.user_id != user_id,  # Исключаем профиль самого пользователя
                # Исключаем профили, которые пользователь уже лайкал или дизлайкал
                ~Profile.user_id.in_(
                    select(Like.target_user_id).where(Like.user_id == user_id)
                ),
                ~Profile.user_id.in_(
                    select(Dislike.target_user_id).where(Dislike.user_id == user_id)
                ),
            )
        )
        .group_by(Profile.profile_id, Profile.user_id, User.user_id)
    )
    
    # Вычисляем итоговый скор с учетом предпочтений
    query = (
        select(
            Profile,
            User,
            func.count(Like.id).label('likes_count'),
            func.count(Dislike.id).label('dislikes_count'),
            (
                (func.count(Like.id) + func.count(Dislike.id))  # Базовый скор активности
                * case(
                    # Множитель за совпадение пола
                    (User.gender == preferred_gender, 2),
                    else_=1,
                )
                * case(
                    # Множитель за совпадение города
                    (User.city_id == user.city_id, 2),
                    else_=1,
                )
                * case(
                    # Множитель за совпадение возрастного диапазона
                    (
                        and_(
                            User.age >= preferred_age_min,
                            User.age <= preferred_age_max,
                        ),
                        2,
                    ),
                    else_=1,
                )
            ).label('total_score'),
        )
        .join(User, Profile.user_id == User.user_id)
        .outerjoin(Like, User.user_id == Like.target_user_id)
        .outerjoin(Dislike, User.user_id == Dislike.target_user_id)
        .where(
            and_(
                Profile.user_id != user_id,  # Исключаем профиль самого пользователя
                # Исключаем профили, которые пользователь уже лайкал или дизлайкал
                ~Profile.user_id.in_(
                    select(Like.target_user_id).where(Like.user_id == user_id)
                ),
                ~Profile.user_id.in_(
                    select(Dislike.target_user_id).where(Dislike.user_id == user_id)
                ),
            )
        )
        .group_by(Profile.profile_id, Profile.user_id, User.user_id)
        .order_by(desc('total_score'))
        .limit(limit)
    )
    
    # Выполняем запрос
    result = await db.execute(query)
    
    # Форматируем результаты
    profiles_data = []
    for profile, matched_user, _likes_count, _dislikes_count, total_score in result:
        profile_dict = {
            'user_id': matched_user.user_id,
            'first_name': matched_user.first_name,
            'age': matched_user.age,
            'gender': matched_user.gender,
            'bio': profile.bio,
            'photo_url': profile.photo_url,
            'score': total_score,  # Добавляем скор для отладки
        }
        profiles_data.append(profile_dict)
    
    if profiles_data:
        # Сохраняем профили в Redis
        await store_user_profiles(user_id, profiles_data)
        logger.info(
            'Loaded and stored %d matching profiles for user %s',
            len(profiles_data),
            user_id,
        )
    else:
        logger.warning('No matching profiles found for user %s', user_id)
    
    return profiles_data 