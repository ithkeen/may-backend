"""Storage domain contracts."""

from may_backend.domain.storage.models import PresignedPutUrl
from may_backend.domain.storage.object_storage import ObjectStorage

__all__ = [
    "ObjectStorage",
    "PresignedPutUrl",
]
