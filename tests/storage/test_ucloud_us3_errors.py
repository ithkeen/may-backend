from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from may_backend.domain.storage import ObjectStorageError, ObjectStorageNotFoundError
from may_backend.infrastructure.s3 import UCloudUS3ObjectStorage


@dataclass(frozen=True)
class _FakeConfig:
    bucket: str = "test-bucket"
    upload_suffix: str = ".example.com"
    public_key: str = "public"
    private_key: str = "private"
    use_https: bool = True
    put_url_expires_seconds: int = 900
    get_url_expires_seconds: int = 900


class _FakeResponse:
    def __init__(
        self,
        *,
        status_code: int,
        reason_phrase: str,
        payload: dict[str, object],
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.reason_phrase = reason_phrase
        self.headers = headers or {}
        self.content = b""
        self._payload = payload

    def json(self) -> dict[str, object]:
        return self._payload


class _FakeClient:
    def __init__(self, response: _FakeResponse) -> None:
        self._response = response

    def request(self, *args: Any, **kwargs: Any) -> _FakeResponse:
        return self._response


def test_ucloud_us3_404_raises_not_found_without_provider_fields() -> None:
    storage = UCloudUS3ObjectStorage(
        config=_FakeConfig(),
        http_client=_FakeClient(
            _FakeResponse(
                status_code=404,
                reason_phrase="Not Found",
                payload={"ErrMsg": "object not found", "RetCode": 404},
                headers={"X-SessionId": "session-123"},
            )
        ),
    )

    with pytest.raises(ObjectStorageNotFoundError) as exc_info:
        storage.head_object("assets/cat.png")

    assert str(exc_info.value) == "object not found"
    assert not hasattr(exc_info.value, "status_code")
    assert not hasattr(exc_info.value, "ret_code")
    assert not hasattr(exc_info.value, "err_msg")
    assert not hasattr(exc_info.value, "session_id")


def test_ucloud_us3_non_404_raises_storage_error_without_provider_fields() -> None:
    storage = UCloudUS3ObjectStorage(
        config=_FakeConfig(),
        http_client=_FakeClient(
            _FakeResponse(
                status_code=500,
                reason_phrase="Internal Server Error",
                payload={"ErrMsg": "backend failed", "RetCode": 500},
                headers={"X-SessionId": "session-456"},
            )
        ),
    )

    with pytest.raises(ObjectStorageError) as exc_info:
        storage.head_object("assets/cat.png")

    assert not isinstance(exc_info.value, ObjectStorageNotFoundError)
    assert str(exc_info.value) == "backend failed"
    assert not hasattr(exc_info.value, "status_code")
    assert not hasattr(exc_info.value, "ret_code")
    assert not hasattr(exc_info.value, "err_msg")
    assert not hasattr(exc_info.value, "session_id")
