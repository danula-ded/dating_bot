import asyncio
import logging
from pathlib import Path

from alembic import command
from alembic.config import Config

from scripts.load_fixtures import main as load_fixtures


async def init_db() -> None:
    # Инициализация Alembic
    alembic_cfg = Config(Path(__file__).parent.parent / "alembic.ini")
    
    try:
        # Создание начальной миграции
        command.revision(alembic_cfg, autogenerate=True, message="Initial migration")
        
        # Применение миграций
        command.upgrade(alembic_cfg, "head")
        
        # Загрузка фикстур
        await load_fixtures()
        
        print("База данных успешно инициализирована")
    except Exception as e:
        logging.exception("Ошибка при инициализации базы данных: %s", e)
        raise


if __name__ == "__main__":
    asyncio.run(init_db()) 