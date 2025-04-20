import asyncio
import logging
import json

from sqlalchemy.exc import IntegrityError

from src.model import meta
from src.storage.db import engine  # Убедись, что engine правильно импортируется

from sqlalchemy import insert
from pathlib import Path
from src.model import City, Interest, User, Profile, Rating, UserInterest


async def load_fixtures(session, model, file_path: str) -> None:
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


async def migrate() -> None:
    try:
        async with engine.begin() as conn:
            # Запуск создания всех таблиц
            await conn.run_sync(meta.metadata.create_all)
            print('Миграции выполнены.')  # Для проверки
            
            fixtures_dir = Path(__file__).parent.parent / "fixtures"
            await load_fixtures(conn, City, fixtures_dir / "cities.json")
            print("Города загружены")
            
            # Загрузка интересов
            await load_fixtures(conn, Interest, fixtures_dir / "interests.json")
            print("Интересы загружены")
            
            # Загрузка пользователей
            await load_fixtures(conn, User, fixtures_dir / "users.json")
            print("Пользователи загружены")
            
            # Загрузка профилей
            await load_fixtures(conn, Profile, fixtures_dir / "profiles.json")
            print("Профили загружены")
            
            # Загрузка рейтингов
            await load_fixtures(conn, Rating, fixtures_dir / "ratings.json")
            print("Рейтинги загружены")
            
            # Загрузка связей пользователей с интересами
            await load_fixtures(conn, UserInterest, fixtures_dir / "user_interests.json")
            print("Связи пользователей с интересами загружены")

    except IntegrityError:
        logging.exception('Ошибка: Таблицы уже существуют')
    except Exception as e:
        logging.exception('Ошибка при выполнении миграции: %s', e)


if __name__ == '__main__':
    asyncio.run(migrate())
