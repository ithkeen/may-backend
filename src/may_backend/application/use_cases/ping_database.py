"""Use case for checking database ping availability."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from may_backend.logger import logger


class DatabasePingRepository(Protocol):
    async def get_ping_message(self) -> str | None:
        """Read the database ping marker message."""
        ...


class DatabasePingUnavailable(RuntimeError):
    """Raised when the database ping check cannot confirm availability."""


@dataclass(frozen=True)
class PingDatabase:
    """Confirm the configured database can serve the expected ping record."""

    repository: DatabasePingRepository

    async def execute(self) -> str:
        try:
            message = await self.repository.get_ping_message()
        except Exception as exc:
            raise DatabasePingUnavailable("database ping query failed") from exc

        if message != "pong":
            logger.error(
                event="supabase.postgres.ping.unavailable",
                reason="missing_ping_record",
                message="database ping record is unavailable",
            )
            raise DatabasePingUnavailable("database ping unavailable")

        return message
