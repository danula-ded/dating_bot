import asyncio
import logging

from sqlalchemy import text

from src.model import Profile, meta
from src.storage.db import engine


async def migrate() -> None:
    try:
        async with engine.begin() as conn:
            # Очистка всех таблиц
            await conn.execute(text('DROP SCHEMA public CASCADE;'))
            await conn.execute(text('CREATE SCHEMA public;'))
            print('Схема очищена')

            # Запуск создания всех таблиц
            await conn.run_sync(meta.metadata.create_all)
            print('Таблицы созданы')

            # Сброс всех последовательностей
            await conn.execute(text('DROP SEQUENCE IF EXISTS profiles_profile_id_seq CASCADE;'))
            await conn.execute(text('CREATE SEQUENCE profiles_profile_id_seq START WITH 1;'))
            await conn.execute(
                text('ALTER TABLE profiles ALTER COLUMN profile_id SET DEFAULT nextval(\'profiles_profile_id_seq\');')
            )
            await conn.execute(text('ALTER SEQUENCE profiles_profile_id_seq OWNED BY profiles.profile_id;'))
            print('Последовательности сброшены')

    except Exception as e:
        logging.exception('Ошибка при выполнении миграции: %s', e)


if __name__ == '__main__':
    asyncio.run(migrate())
