"""Object-storage FastAPI dependencies."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from may_backend.application.use_cases.storage import CreatePresignedPutUrl
from may_backend.infrastructure.s3 import UCloudUS3ObjectStorage


def get_create_presigned_put_url() -> CreatePresignedPutUrl:
    return CreatePresignedPutUrl(object_storage=UCloudUS3ObjectStorage())


CreatePresignedPutUrlDep = Annotated[
    CreatePresignedPutUrl,
    Depends(get_create_presigned_put_url),
]
