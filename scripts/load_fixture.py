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
        await load_fixture(paths, session)


if __name__ == '__main__':
    asyncio.run(
        main(
            [
                Path('fixtures/public.file_records.json'),
            ]
        )
    )
