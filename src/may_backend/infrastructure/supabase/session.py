"""Supabase Postgres async session management."""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from may_backend.config import supabase_config
from may_backend.logger import logger


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def make_supabase_database_url(database_url: str) -> str:
    value = database_url.strip()
    if not value:
        raise ValueError("DATABASE_URL is required")

    url = make_url(value)
    if url.drivername in {"postgres", "postgresql"}:
        url = url.set(drivername="postgresql+asyncpg")
    elif url.drivername != "postgresql+asyncpg":
        raise ValueError("DATABASE_URL must be a PostgreSQL URL")

    query = dict(url.query)
    sslmode = query.pop("sslmode", None)
    if sslmode is not None and "ssl" not in query:
        query["ssl"] = _query_value(sslmode)

    query.setdefault("prepared_statement_cache_size", "0")
    return url.set(query=query).render_as_string(hide_password=False)


def initialize_supabase() -> None:
    global _engine, _session_factory

    if _engine is not None and _session_factory is not None:
        return

    try:
        database_url = make_supabase_database_url(supabase_config.database_url)
        _engine = create_async_engine(database_url, pool_pre_ping=True)
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    except Exception as exc:
        logger.error(
            event="supabase.postgres.engine.failed",
            error_code=type(exc).__name__,
            message="failed to initialize supabase postgres engine",
        )
        raise

    logger.info(event="supabase.postgres.engine.initialized")


async def close_supabase() -> None:
    global _engine, _session_factory

    if _engine is None:
        return

    await _engine.dispose()
    _engine = None
    _session_factory = None
    logger.info(event="supabase.postgres.engine.closed")


async def get_supabase_session() -> AsyncIterator[AsyncSession]:
    if _session_factory is None:
        initialize_supabase()

    if _session_factory is None:
        raise RuntimeError("Supabase session factory is not initialized")

    async with _session_factory() as session:
        yield session


def _query_value(value: str | tuple[str, ...]) -> str:
    if isinstance(value, tuple):
        return value[0]
    return value
