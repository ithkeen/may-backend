"""UCloud US3 object storage adapter."""

from __future__ import annotations

import base64
import hashlib
import hmac
import re
import time
from datetime import UTC, datetime
from typing import Protocol
from urllib.parse import quote, urlencode

from may_backend.config import ucloud_us3_config
from may_backend.domain.storage.models import PresignedPutUrl


_ALLOWED_CONTENT_TYPES = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/webp",
    }
)
_KEY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._~/-]{0,1022}$")
_MIN_EXPIRES_SECONDS = 60
_MAX_EXPIRES_SECONDS = 3600


class _UCloudUS3ConfigLike(Protocol):
    bucket: str
    upload_suffix: str
    public_key: str
    private_key: str
    use_https: bool
    put_url_expires_seconds: int


class UCloudUS3ObjectStorage:
    def __init__(
        self,
        config: _UCloudUS3ConfigLike = ucloud_us3_config,
    ) -> None:
        self._bucket = self._required("bucket", config.bucket)
        self._upload_suffix = self._required(
            "upload_suffix",
            config.upload_suffix,
        )
        self._public_key = self._required(
            "public_key",
            config.public_key,
        )
        self._private_key = self._required(
            "private_key",
            config.private_key,
        )
        self._use_https = config.use_https
        self._default_put_url_expires_seconds = self._validate_expires_seconds(
            config.put_url_expires_seconds
        )

        if not self._upload_suffix.startswith("."):
            raise ValueError("upload_suffix must start with '.'")

    def create_presigned_put_url(
        self,
        key: str,
        *,
        content_type: str,
        expires_in_seconds: int | None = None,
    ) -> PresignedPutUrl:
        object_key = self._validate_key(key)
        object_content_type = self._validate_content_type(content_type)
        resolved_expires_seconds = self._validate_expires_seconds(
            expires_in_seconds
            if expires_in_seconds is not None
            else self._default_put_url_expires_seconds
        )
        expires_unix_timestamp = int(time.time()) + resolved_expires_seconds
        signature = self._sign_put_url(
            key=object_key,
            content_type=object_content_type,
            expires_unix_timestamp=expires_unix_timestamp,
        )
        scheme = "https" if self._use_https else "http"
        encoded_key = quote(object_key, safe="/._~-")
        query = urlencode(
            {
                "UCloudPublicKey": self._public_key,
                "Expires": str(expires_unix_timestamp),
                "Signature": signature,
            }
        )
        url = (
            f"{scheme}://{self._bucket}{self._upload_suffix}/{encoded_key}?{query}"
        )

        return PresignedPutUrl(
            url=url,
            method="PUT",
            headers={"Content-Type": object_content_type},
            key=object_key,
            expires_at=datetime.fromtimestamp(expires_unix_timestamp, tz=UTC),
            expires_in_seconds=resolved_expires_seconds,
        )

    def _sign_put_url(
        self,
        *,
        key: str,
        content_type: str,
        expires_unix_timestamp: int,
    ) -> str:
        string_to_sign = "\n".join(
            [
                "PUT",
                "",
                content_type,
                str(expires_unix_timestamp),
                f"/{self._bucket}/{key}",
            ]
        )
        digest = hmac.new(
            self._private_key.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            hashlib.sha1,
        ).digest()
        return base64.b64encode(digest).decode("utf-8")

    @staticmethod
    def _required(name: str, value: str) -> str:
        normalized_value = value.strip()
        if not normalized_value:
            raise ValueError(f"{name} is required")
        return normalized_value

    @staticmethod
    def _validate_key(key: str) -> str:
        if not _KEY_PATTERN.fullmatch(key):
            raise ValueError(
                "key must be 1-1023 characters and use URL-safe path characters"
            )
        if "//" in key:
            raise ValueError("key must not contain empty path segments")
        return key

    @staticmethod
    def _validate_content_type(content_type: str) -> str:
        normalized_content_type = content_type.strip().lower()
        if normalized_content_type not in _ALLOWED_CONTENT_TYPES:
            allowed_types = ", ".join(sorted(_ALLOWED_CONTENT_TYPES))
            raise ValueError(f"content_type must be one of: {allowed_types}")
        return normalized_content_type

    @staticmethod
    def _validate_expires_seconds(expires_in_seconds: int) -> int:
        if not (
            _MIN_EXPIRES_SECONDS
            <= expires_in_seconds
            <= _MAX_EXPIRES_SECONDS
        ):
            raise ValueError(
                "expires_in_seconds must be between "
                f"{_MIN_EXPIRES_SECONDS} and {_MAX_EXPIRES_SECONDS}"
            )
        return expires_in_seconds
