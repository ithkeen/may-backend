"""Application service registry."""

from __future__ import annotations

from dataclasses import dataclass

from may_backend.application.use_cases import CreatePresignedPutUrl
from may_backend.domain.storage import ObjectStorage


@dataclass(frozen=True)
class ApplicationServices:
    """Expose application use cases from shared application dependencies."""

    object_storage: ObjectStorage

    @property
    def create_presigned_put_url(self) -> CreatePresignedPutUrl:
        return CreatePresignedPutUrl(object_storage=self.object_storage)
