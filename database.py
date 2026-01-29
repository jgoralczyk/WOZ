from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlmodel import SQLModel
from typing import AsyncGenerator
import os

# Import models to ensure they're registered with SQLModel.metadata
# This must happen before init_db() is called
from models import Wniosek, User  # noqa: F401

# SQLite dla developmentu lokalnego (działa out-of-the-box na Windows)
# PostgreSQL dla produkcji (ustaw DATABASE_URL)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./wnioski.db")


engine = create_async_engine(DATABASE_URL, echo=True)

SessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session