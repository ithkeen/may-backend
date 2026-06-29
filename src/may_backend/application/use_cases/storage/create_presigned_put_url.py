"""Use case for creating presigned object upload URLs."""

from __future__ import annotations

from dataclasses import dataclass

from may_backend.domain.storage import ObjectStorage, PresignedPutUrl


@dataclass(frozen=True)
class CreatePresignedPutUrl:
    """Create a short-lived URL for client-side object uploads."""

    object_storage: ObjectStorage

    def execute(
        self,
        *,
        key: str,
        content_type: str,
        expires_in_seconds: int | None = None,
    ) -> PresignedPutUrl:
        return self.object_storage.create_presigned_put_url(
            key,
            content_type=content_type,
            expires_in_seconds=expires_in_seconds,
        )
