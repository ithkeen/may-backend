"""Supabase Postgres database ping repository."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from may_backend.logger import logger


@dataclass(frozen=True)
class SupabasePingRepository:
    session: AsyncSession

    async def get_ping_message(self) -> str | None:
        try:
            result = await self.session.execute(
                text("select message from ping where id = :id"),
                {"id": 1},
            )
        except SQLAlchemyError as exc:
            logger.error(
                event="supabase.postgres.ping.failed",
                error_code=type(exc).__name__,
                message="database ping query failed",
            )
            raise

        return result.scalar_one_or_none()
