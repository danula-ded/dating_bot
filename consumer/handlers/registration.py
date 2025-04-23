from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from consumer.logger import logger
from consumer.schema.registration import RegistrationMessage
from consumer.storage.db import async_session
from src.model.city import City
from src.model.profile import Profile
from src.model.user import User


async def get_or_create_city(db: AsyncSession, city_name: str | None) -> City:
    """Получает существующий город или создает новый."""
    # Если city_name не указан, используем 'Не указан' как значение по умолчанию
    if not city_name:
        city_name = 'Сочи'
    
    # Ищем город по имени
    result = await db.execute(select(City).where(City.name == city_name))
    city = result.scalar_one_or_none()

    if city is None:
        # Если город не найден, создаем новый
        city = City(name=city_name)
        db.add(city)
        await db.flush()  # Получаем ID нового города

    return city


async def handle_registration(message: RegistrationMessage) -> None:
    """Обрабатывает сообщение о регистрации пользователя и сохраняет данные в БД."""
    try:
        async with async_session() as db:
            # Получаем или создаем город
            city = await get_or_create_city(db, message.user.city_name)

            # Проверяем и форматируем username
            username = message.user.username
            if username and not username.startswith('@'):
                username = f'@{username}'

            # Проверяем существование пользователя
            result = await db.execute(select(User).where(User.user_id == message.user.user_id))
            existing_user = result.scalar_one_or_none()

            if existing_user:
                # Обновляем существующего пользователя
                existing_user.first_name = message.user.first_name
                existing_user.age = message.user.age
                existing_user.gender = message.user.gender
                existing_user.city_id = city.city_id
                existing_user.username = username
            else:
                # Создаем нового пользователя
                user = User(
                    user_id=message.user.user_id,
                    username=username,
                    first_name=message.user.first_name,
                    age=message.user.age,
                    gender=message.user.gender,
                    city_id=city.city_id,
                )
                db.add(user)
                await db.flush()  # Получаем ID нового пользователя

            # Проверяем существование профиля
            result = await db.execute(select(Profile).where(Profile.user_id == message.profile.user_id))
            existing_profile = result.scalar_one_or_none()

            if existing_profile:
                # Обновляем существующий профиль
                existing_profile.bio = message.profile.bio
                existing_profile.photo_url = message.profile.photo_url
                existing_profile.preferred_gender = message.profile.preferred_gender
                existing_profile.preferred_age_min = message.profile.preferred_age_min
                existing_profile.preferred_age_max = message.profile.preferred_age_max
            else:
                # Создаем новый профиль без указания profile_id
                profile = Profile(
                    user_id=message.profile.user_id,
                    bio=message.profile.bio,
                    photo_url=message.profile.photo_url,
                    preferred_gender=message.profile.preferred_gender,
                    preferred_age_min=message.profile.preferred_age_min,
                    preferred_age_max=message.profile.preferred_age_max,
                )
                db.add(profile)
                await db.flush()  # Получаем ID нового профиля

            # Сохраняем изменения
            await db.commit()

        logger.info('Пользователь %s успешно зарегистрирован/обновлен. Профиль создан/обновлен.', message.user.user_id)
    except Exception as e:
        logger.error('Ошибка при регистрации пользователя %s: %s', message.user.user_id, e)
        raise
