"""FastAPI dependency wiring."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from may_backend.application import ApplicationServices
from may_backend.domain.storage import ObjectStorage
from may_backend.infrastructure.s3 import UCloudUS3ObjectStorage


def get_object_storage() -> ObjectStorage:
    return UCloudUS3ObjectStorage()


def get_application_services(
    object_storage: Annotated[ObjectStorage, Depends(get_object_storage)],
) -> ApplicationServices:
    return ApplicationServices(object_storage=object_storage)


ApplicationServicesDep = Annotated[
    ApplicationServices,
    Depends(get_application_services),
]
