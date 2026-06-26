"""Storage domain contracts."""

from may_backend.domain.storage.models import (
    ObjectMetadata,
    ObjectStorageError,
    ObjectStorageNotFoundError,
    PresignedGetUrl,
    PresignedPutUrl,
    PutObjectResult,
    StoredObject,
)
from may_backend.domain.storage.object_storage import ObjectStorage

__all__ = [
    "ObjectMetadata",
    "ObjectStorage",
    "ObjectStorageError",
    "ObjectStorageNotFoundError",
    "PresignedGetUrl",
    "PresignedPutUrl",
    "PutObjectResult",
    "StoredObject",
]
