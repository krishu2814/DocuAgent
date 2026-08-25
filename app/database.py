from collections.abc import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


def get_async_database_url(url: str) -> str:
    """Ensures database URL uses the asyncpg driver."""
    clean_url = url.strip()
    if clean_url.startswith("postgres://"):
        return clean_url.replace("postgres://", "postgresql+asyncpg://", 1)
    if clean_url.startswith("postgresql://") and not clean_url.startswith("postgresql+asyncpg://"):
        return clean_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return clean_url


engine = create_async_engine(
    get_async_database_url(settings.DATABASE_URL),
    echo=False,
    future=True,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
