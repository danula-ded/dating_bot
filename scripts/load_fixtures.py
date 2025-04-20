import asyncio
import json
from pathlib import Path

# from sqlalchemy import insert, text, delete
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.model import City, Interest, User, Profile, Rating, UserInterest
from src.storage.db import async_session_maker


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


async def load_fixtures(session: AsyncSession, model, file_path: str) -> None:
    try:
        print(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        await session.execute(insert(model), data)
        await session.commit()
        print(f"Successfully loaded data from {file_path}")
    except Exception as e:
        print(f"Error loading data from {file_path}: {str(e)}")
        raise


async def main() -> None:
    fixtures_dir = Path(__file__).parent.parent / "fixtures"
    
    async with async_session_maker() as session:
        # Очищаем таблицы
        # await clear_tables(session)
        
        # # Сброс последовательностей
        # await reset_sequences(session)
        
        # Загрузка городов
        await load_fixtures(session, City, fixtures_dir / "cities.json")
        print("Города загружены")
        
        # Загрузка интересов
        await load_fixtures(session, Interest, fixtures_dir / "interests.json")
        print("Интересы загружены")
        
        # Загрузка пользователей
        await load_fixtures(session, User, fixtures_dir / "users.json")
        print("Пользователи загружены")
        
        # Загрузка профилей
        await load_fixtures(session, Profile, fixtures_dir / "profiles.json")
        print("Профили загружены")
        
        # Загрузка рейтингов
        await load_fixtures(session, Rating, fixtures_dir / "ratings.json")
        print("Рейтинги загружены")
        
        # Загрузка связей пользователей с интересами
        await load_fixtures(session, UserInterest, fixtures_dir / "user_interests.json")
        print("Связи пользователей с интересами загружены")


if __name__ == "__main__":
    asyncio.run(main()) 