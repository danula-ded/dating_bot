import asyncio
import json
from pathlib import Path

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.model import City, Interest
from src.storage.db import async_session_maker


async def load_fixtures(session: AsyncSession, model, file_path: str) -> None:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    await session.execute(insert(model), data)
    await session.commit()


async def main() -> None:
    fixtures_dir = Path(__file__).parent.parent / "fixtures"
    
    async with async_session_maker() as session:
        # Загрузка городов
        await load_fixtures(session, City, fixtures_dir / "cities.json")
        print("Города загружены")
        
        # Загрузка интересов
        await load_fixtures(session, Interest, fixtures_dir / "interests.json")
        print("Интересы загружены")


if __name__ == "__main__":
    asyncio.run(main()) 