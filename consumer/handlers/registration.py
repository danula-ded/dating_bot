from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from consumer.logger import logger
from consumer.schema.registration import RegistrationMessage
from consumer.storage.db import async_session
from src.model.user import User
from src.model.profile import Profile
from src.model.city import City


async def get_or_create_city(db: AsyncSession, city_name: str) -> City:
    """Получает существующий город или создает новый."""
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
            
            # Создаем запись пользователя
            user = User(
                user_id=message.user.user_id,
                first_name=message.user.first_name,
                last_name=message.user.last_name,
                age=message.user.age,
                gender=message.user.gender,
                city_id=city.city_id
            )
            db.add(user)
            
            # Создаем запись профиля
            profile = Profile(
                user_id=message.profile.user_id,
                bio=message.profile.bio,
                photo_url=message.profile.photo_url,
                preferred_gender=message.profile.preferred_gender,
                preferred_age_min=message.profile.preferred_age_min,
                preferred_age_max=message.profile.preferred_age_max
            )
            db.add(profile)
            
            # Сохраняем изменения
            await db.commit()
            
        logger.info(
            'Пользователь %s успешно зарегистрирован. Профиль создан.',
            message.user.user_id
        )
    except Exception as e:
        logger.error(
            'Ошибка при регистрации пользователя %s: %s',
            message.user.user_id,
            e
        )
        raise 