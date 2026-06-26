"""Object storage abstraction required by the domain."""

from __future__ import annotations

from typing import Protocol

from may_backend.domain.storage.models import (
    ObjectMetadata,
    PresignedGetUrl,
    PresignedPutUrl,
    PutObjectResult,
    StoredObject,
)


class ObjectStorage(Protocol):
    def create_presigned_put_url(
        self,
        key: str,
        *,
        content_type: str,
        expires_in_seconds: int | None = None,
    ) -> PresignedPutUrl:
        """Create a short-lived URL for uploading an object with PUT."""
        ...

    def create_presigned_get_url(
        self,
        key: str,
        *,
        expires_in_seconds: int | None = None,
    ) -> PresignedGetUrl:
        """Create a short-lived URL for downloading an object with GET."""
        ...

    def put_object(
        self,
        key: str,
        *,
        body: bytes,
        content_type: str,
    ) -> PutObjectResult:
        """Upload an object directly through the storage backend."""
        ...

    def get_object(self, key: str) -> StoredObject:
        """Download an object directly through the storage backend."""
        ...

    def head_object(self, key: str) -> ObjectMetadata:
        """Fetch object metadata without downloading the object body."""
        ...

    def delete_object(self, key: str) -> None:
        """Delete an object from the storage backend."""
        ...
