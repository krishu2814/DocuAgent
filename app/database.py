from collections.abc import AsyncGenerator
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


def get_async_database_url_and_args(url: str) -> tuple[str, dict]:
    """Cleans database URL and converts query parameters for asyncpg compatibility."""
    clean_url = url.strip()

    # Convert standard postgres/postgresql scheme to postgresql+asyncpg
    if clean_url.startswith("postgres://"):
        clean_url = clean_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif clean_url.startswith("postgresql://") and not clean_url.startswith("postgresql+asyncpg://"):
        clean_url = clean_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    connect_args: dict = {}
    parsed = urlparse(clean_url)
    query_params = parse_qs(parsed.query)

    # asyncpg does not accept sslmode query parameter; extract and use connect_args['ssl']
    if "sslmode" in query_params:
        sslmode_val = query_params.pop("sslmode")[0]
        if sslmode_val in ["require", "verify-ca", "verify-full", "prefer"]:
            connect_args["ssl"] = "require"

    if "ssl" in query_params:
        ssl_val = query_params.pop("ssl")[0]
        if ssl_val.lower() in ["require", "true", "1"]:
            connect_args["ssl"] = "require"

    new_query = urlencode(query_params, doseq=True)
    clean_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment,
    ))

    # Auto-enable SSL for cloud databases (Neon, Supabase, Render)
    is_local = any(h in clean_url for h in ["localhost", "127.0.0.1", "@postgres:"])
    if not is_local and "ssl" not in connect_args:
        connect_args["ssl"] = "require"

    return clean_url, connect_args


db_url, db_connect_args = get_async_database_url_and_args(settings.DATABASE_URL)

engine = create_async_engine(
    db_url,
    connect_args=db_connect_args,
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
