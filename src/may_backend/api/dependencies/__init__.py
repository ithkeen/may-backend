"""FastAPI dependency wiring."""

from may_backend.api.dependencies.database import (
    PingDatabaseDep,
    SupabaseSessionDep,
    get_ping_database,
)
from may_backend.api.dependencies.storage import (
    CreatePresignedPutUrlDep,
    get_create_presigned_put_url,
)

__all__ = [
    "CreatePresignedPutUrlDep",
    "PingDatabaseDep",
    "SupabaseSessionDep",
    "get_create_presigned_put_url",
    "get_ping_database",
]
