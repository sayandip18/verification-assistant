from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# Neon's pooled host runs PgBouncer in transaction mode, which doesn't support
# asyncpg's prepared-statement cache, so turn it off for pooled connections.
_connect_args = {"statement_cache_size": 0} if "-pooler" in settings.database_url else {}

engine = create_async_engine(
    settings.database_url, echo=False, pool_pre_ping=True, connect_args=_connect_args
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
