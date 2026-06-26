"""Storage domain data models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Mapping


@dataclass(frozen=True)
class PresignedPutUrl:
    url: str
    method: Literal["PUT"]
    headers: Mapping[str, str]
    key: str
    expires_at: datetime
    expires_in_seconds: int


@dataclass(frozen=True)
class PresignedGetUrl:
    url: str
    method: Literal["GET"]
    headers: Mapping[str, str]
    key: str
    expires_at: datetime
    expires_in_seconds: int


@dataclass(frozen=True)
class PutObjectResult:
    key: str
    etag: str | None


@dataclass(frozen=True)
class ObjectMetadata:
    key: str
    content_type: str | None
    content_length: int | None
    etag: str | None
    last_modified: datetime | None
    storage_class: str | None
    metadata: Mapping[str, str]


@dataclass(frozen=True)
class StoredObject:
    key: str
    body: bytes
    content_type: str | None
    content_length: int
    etag: str | None
    metadata: Mapping[str, str]


class ObjectStorageError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        ret_code: int | None = None,
        err_msg: str | None = None,
        session_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.ret_code = ret_code
        self.err_msg = err_msg
        self.session_id = session_id


class ObjectStorageNotFoundError(ObjectStorageError):
    """Raised when an object does not exist in object storage."""
