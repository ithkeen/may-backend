"""FastAPI dependency wiring."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from may_backend.application import ApplicationServices
from may_backend.application.use_cases.ping_database import DatabasePingRepository
from may_backend.domain.storage import ObjectStorage
from may_backend.infrastructure.s3 import UCloudUS3ObjectStorage
from may_backend.infrastructure.supabase import (
    SupabasePingRepository,
    get_supabase_session,
)


def get_object_storage() -> ObjectStorage:
    return UCloudUS3ObjectStorage()


def get_database_ping_repository(
    session: Annotated[AsyncSession, Depends(get_supabase_session)],
) -> DatabasePingRepository:
    return SupabasePingRepository(session=session)


def get_application_services(
    object_storage: Annotated[ObjectStorage, Depends(get_object_storage)],
    database_ping_repository: Annotated[
        DatabasePingRepository,
        Depends(get_database_ping_repository),
    ],
) -> ApplicationServices:
    return ApplicationServices(
        object_storage=object_storage,
        database_ping_repository=database_ping_repository,
    )


ApplicationServicesDep = Annotated[
    ApplicationServices,
    Depends(get_application_services),
]
