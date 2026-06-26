"""Object storage abstraction required by the domain."""

from __future__ import annotations

from typing import Protocol

from may_backend.domain.storage.models import PresignedPutUrl


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
