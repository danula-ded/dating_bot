import asyncio
import json
import logging
from pathlib import Path

from sqlalchemy import insert, text
from sqlalchemy.exc import IntegrityError

from src.model import City, Interest, Profile, Rating, User, UserInterest, meta
from src.storage.db import engine


async def load_fixtures(session, model, file_path: str) -> None:
    try:
        print(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Используем ON CONFLICT DO NOTHING для всех моделей
        stmt = insert(model).on_conflict_do_nothing()
        await session.execute(stmt, data)
        await session.commit()
        print(f"Successfully loaded data from {file_path}")
    except Exception as e:
        print(f"Error loading data from {file_path}: {str(e)}")
        raise


async def migrate() -> None:
    try:
        async with engine.begin() as conn:
            # Очистка всех таблиц
            await conn.execute(text("DROP SCHEMA public CASCADE;"))
            await conn.execute(text("CREATE SCHEMA public;"))
            print('Схема очищена')

            # Запуск создания всех таблиц
            await conn.run_sync(meta.metadata.create_all)
            await conn.commit()  # Явно коммитим создание таблиц
            print('Таблицы созданы')

            fixtures_dir = Path(__file__).parent.parent / "fixtures"

            # Загрузка городов
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

    except Exception as e:
        logging.exception('Ошибка при выполнении миграции: %s', e)


if __name__ == '__main__':
    asyncio.run(migrate())
