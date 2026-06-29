"""Database-related FastAPI dependencies."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from may_backend.application.use_cases.health import PingDatabase
from may_backend.infrastructure.supabase import (
    SupabasePingRepository,
    get_supabase_session,
)


SupabaseSessionDep = Annotated[AsyncSession, Depends(get_supabase_session)]


def get_ping_database(
    session: SupabaseSessionDep,
) -> PingDatabase:
    return PingDatabase(repository=SupabasePingRepository(session=session))


PingDatabaseDep = Annotated[PingDatabase, Depends(get_ping_database)]
