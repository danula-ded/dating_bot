import asyncio
import json
from pathlib import Path

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.model import meta
from src.storage.db import async_session


# NOTE: Не использовать для прода. Нужно использовать alembic
async def load_fixture(files: list[Path], session: AsyncSession) -> None:
    for file in files:
        with open(file, 'r') as f:
            table = meta.metadata.tables[file.stem]
            await session.execute(insert(table).values(json.load(f)))
            await session.commit()


async def main(paths: list[Path]) -> None:
    async with async_session() as session:
        print(paths)
        await load_fixture(paths, session)


if __name__ == '__main__':
    asyncio.run(
        main(
            [
                Path('fixtures/cities.json'),
                Path('fixtures/interests.json'),
                Path('fixtures/users.json'),
                Path('fixtures/profiles.json'),
                Path('fixtures/ratings.json'),
                Path('fixtures/user_interests.json'),
                Path('fixtures/public.file_records.json'),
            ]
        )
    )
