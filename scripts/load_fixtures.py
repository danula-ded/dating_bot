import asyncio
import json
from pathlib import Path

# from sqlalchemy import insert, text, delete
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.model import City, Interest, Profile, Rating, User, UserInterest
from src.storage.db import async_session

# async def clear_tables(session: AsyncSession) -> None:
#     # Очищаем таблицы в правильном порядке (с учетом внешних ключей)
#     await session.execute(delete(UserInterest))
#     await session.execute(delete(Rating))
#     await session.execute(delete(Profile))
#     await session.execute(delete(User))
#     await session.execute(delete(Interest))
#     await session.execute(delete(City))
#     await session.commit()
#     print("Таблицы очищены")


# async def reset_sequences(session: AsyncSession) -> None:
#     # Сброс последовательностей для всех таблиц
#     await session.execute(text("ALTER SEQUENCE cities_city_id_seq RESTART WITH 1"))
#     await session.execute(text("ALTER SEQUENCE interests_interest_id_seq RESTART WITH 1"))
#     await session.execute(text("ALTER SEQUENCE profiles_profile_id_seq RESTART WITH 1"))
#     await session.execute(text("ALTER SEQUENCE ratings_rating_id_seq RESTART WITH 1"))
#     await session.commit()
#     print("Последовательности сброшены")


async def get_or_create_city(session: AsyncSession, city_name: str) -> City:
    """Получает существующий город или создает новый."""
    # Ищем город по имени
    result = await session.execute(select(City).where(City.name == city_name))
    city = result.scalar_one_or_none()

    if city is None:
        # Если город не найден, создаем новый
        city = City(name=city_name)
        session.add(city)
        await session.flush()  # Получаем ID нового города

    return city


async def get_or_create_interest(session: AsyncSession, interest_name: str) -> Interest:
    """Получает существующий интерес или создает новый."""
    # Ищем интерес по имени
    result = await session.execute(select(Interest).where(Interest.name == interest_name))
    interest = result.scalar_one_or_none()

    if interest is None:
        # Если интерес не найден, создаем новый
        interest = Interest(name=interest_name)
        session.add(interest)
        await session.flush()  # Получаем ID нового интереса

    return interest


async def get_or_create_user(session: AsyncSession, user_data: dict) -> User:
    """Получает существующего пользователя или создает нового."""
    # Ищем пользователя по ID
    result = await session.execute(select(User).where(User.user_id == user_data['user_id']))
    user = result.scalar_one_or_none()

    if user is None:
        # Если пользователь не найден, создаем нового
        user = User(**user_data)
        session.add(user)
        await session.flush()  # Получаем ID нового пользователя

    return user


async def get_or_create_profile(session: AsyncSession, profile_data: dict) -> Profile:
    """Получает существующий профиль или создает новый."""
    # Ищем профиль по ID
    result = await session.execute(select(Profile).where(Profile.profile_id == profile_data['profile_id']))
    profile = result.scalar_one_or_none()

    if profile is None:
        # Если профиль не найден, создаем новый
        profile = Profile(**profile_data)
        session.add(profile)
        await session.flush()  # Получаем ID нового профиля

    return profile


async def get_or_create_rating(session: AsyncSession, rating_data: dict) -> Rating:
    """Получает существующий рейтинг или создает новый."""
    # Ищем рейтинг по ID
    result = await session.execute(select(Rating).where(Rating.rating_id == rating_data['rating_id']))
    rating = result.scalar_one_or_none()

    if rating is None:
        # Если рейтинг не найден, создаем новый
        rating = Rating(**rating_data)
        session.add(rating)
        await session.flush()  # Получаем ID нового рейтинга

    return rating


async def get_or_create_user_interest(session: AsyncSession, user_id: int, interest_id: int) -> UserInterest:
    """Получает существующую связь пользователя с интересом или создает новую."""
    # Ищем связь по user_id и interest_id
    result = await session.execute(
        select(UserInterest).where(UserInterest.user_id == user_id, UserInterest.interest_id == interest_id)
    )
    user_interest = result.scalar_one_or_none()

    if user_interest is None:
        # Если связь не найдена, создаем новую
        user_interest = UserInterest(user_id=user_id, interest_id=interest_id)
        session.add(user_interest)
        await session.flush()  # Получаем ID новой связи

    return user_interest


async def load_cities(session: AsyncSession, file_path: str) -> None:
    """Загружает города с проверкой на существование."""
    try:
        print(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            cities_data = json.load(f)

        for city_data in cities_data:
            await get_or_create_city(session, city_data['name'])

        await session.commit()
        print(f"Successfully loaded cities from {file_path}")
    except Exception as e:
        print(f"Error loading cities from {file_path}: {str(e)}")
        raise


async def load_interests(session: AsyncSession, file_path: str) -> None:
    """Загружает интересы с проверкой на существование."""
    try:
        print(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            interests_data = json.load(f)

        for interest_data in interests_data:
            await get_or_create_interest(session, interest_data['name'])

        await session.commit()
        print(f"Successfully loaded interests from {file_path}")
    except Exception as e:
        print(f"Error loading interests from {file_path}: {str(e)}")
        raise


async def load_users(session: AsyncSession, file_path: str) -> None:
    """Загружает пользователей с проверкой на существование."""
    try:
        print(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            users_data = json.load(f)

        for user_data in users_data:
            await get_or_create_user(session, user_data)

        await session.commit()
        print(f"Successfully loaded users from {file_path}")
    except Exception as e:
        print(f"Error loading users from {file_path}: {str(e)}")
        raise


async def load_profiles(session: AsyncSession, file_path: str) -> None:
    """Загружает профили с проверкой на существование."""
    try:
        print(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            profiles_data = json.load(f)

        for profile_data in profiles_data:
            await get_or_create_profile(session, profile_data)

        await session.commit()
        print(f"Successfully loaded profiles from {file_path}")
    except Exception as e:
        print(f"Error loading profiles from {file_path}: {str(e)}")
        raise


async def load_ratings(session: AsyncSession, file_path: str) -> None:
    """Загружает рейтинги с проверкой на существование."""
    try:
        print(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            ratings_data = json.load(f)

        for rating_data in ratings_data:
            await get_or_create_rating(session, rating_data)

        await session.commit()
        print(f"Successfully loaded ratings from {file_path}")
    except Exception as e:
        print(f"Error loading ratings from {file_path}: {str(e)}")
        raise


async def load_user_interests(session: AsyncSession, file_path: str) -> None:
    """Загружает связи пользователей с интересами с проверкой на существование."""
    try:
        print(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            user_interests_data = json.load(f)

        for user_interest_data in user_interests_data:
            await get_or_create_user_interest(session, user_interest_data['user_id'], user_interest_data['interest_id'])

        await session.commit()
        print(f"Successfully loaded user interests from {file_path}")
    except Exception as e:
        print(f"Error loading user interests from {file_path}: {str(e)}")
        raise


async def load_fixtures(session: AsyncSession, model, file_path: str) -> None:
    """Загружает фикстуры для остальных моделей."""
    try:
        print(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Используем insert().on_conflict_do_nothing() для безопасной вставки
        stmt = insert(model).on_conflict_do_nothing()
        await session.execute(stmt, data)
        await session.commit()
        print(f"Successfully loaded data from {file_path}")
    except Exception as e:
        print(f"Error loading data from {file_path}: {str(e)}")
        raise


async def main() -> None:
    fixtures_dir = Path(__file__).parent.parent / "fixtures"

    async with async_session() as session:
        # Очищаем таблицы
        # await clear_tables(session)

        # # Сброс последовательностей
        # await reset_sequences(session)

        # Загрузка городов
        await load_cities(session, fixtures_dir / "cities.json")
        print("Города загружены")

        # Загрузка интересов
        await load_interests(session, fixtures_dir / "interests.json")
        print("Интересы загружены")

        # Загрузка пользователей
        await load_users(session, fixtures_dir / "users.json")
        print("Пользователи загружены")

        # Загрузка профилей
        await load_profiles(session, fixtures_dir / "profiles.json")
        print("Профили загружены")

        # Загрузка рейтингов
        await load_ratings(session, fixtures_dir / "ratings.json")
        print("Рейтинги загружены")

        # Загрузка связей пользователей с интересами
        await load_user_interests(session, fixtures_dir / "user_interests.json")
        print("Связи пользователей с интересами загружены")


if __name__ == "__main__":
    asyncio.run(main())
