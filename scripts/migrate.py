import asyncio
import logging

from sqlalchemy.exc import IntegrityError

from src.model import meta
from src.storage.db import engine  # Убедись, что engine правильно импортируется


async def migrate() -> None:
    try:
        async with engine.begin() as conn:
            # Запуск создания всех таблиц
            await conn.run_sync(meta.metadata.create_all)
            print('Миграции выполнены.')  # Для проверки
    except IntegrityError:
        logging.exception('Ошибка: Таблицы уже существуют')
    except Exception as e:
        logging.exception('Ошибка при выполнении миграции: %s', e)


if __name__ == '__main__':
    asyncio.run(migrate())
