"""UCloud US3 object storage adapter."""

from __future__ import annotations

import base64
import hashlib
import hmac
import re
import time
from collections.abc import Mapping
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import NoReturn, Protocol
from urllib.parse import quote, urlencode

import httpx2

from may_backend.config import ucloud_us3_config
from may_backend.domain.storage.models import (
    ObjectMetadata,
    ObjectStorageError,
    ObjectStorageNotFoundError,
    PresignedGetUrl,
    PresignedPutUrl,
    PutObjectResult,
    StoredObject,
)
from may_backend.logger import logger


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
_USER_METADATA_HEADER_PREFIX = "x-ufile-meta-"


class _UCloudUS3ConfigLike(Protocol):
    bucket: str
    upload_suffix: str
    public_key: str
    private_key: str
    use_https: bool
    put_url_expires_seconds: int
    get_url_expires_seconds: int


class UCloudUS3ObjectStorage:
    def __init__(
        self,
        config: _UCloudUS3ConfigLike = ucloud_us3_config,
        *,
        http_client: httpx2.Client | None = None,
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
        self._default_get_url_expires_seconds = self._validate_expires_seconds(
            getattr(
                config,
                "get_url_expires_seconds",
                config.put_url_expires_seconds,
            )
        )
        self._http_client = http_client

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
        resolved_expires_seconds = self._resolve_expires_seconds(
            expires_in_seconds,
            default_expires_seconds=self._default_put_url_expires_seconds,
        )
        expires_unix_timestamp = int(time.time()) + resolved_expires_seconds
        url = self._presigned_url(
            method="PUT",
            key=object_key,
            content_md5="",
            content_type=object_content_type,
            expires_unix_timestamp=expires_unix_timestamp,
        )

        return PresignedPutUrl(
            url=url,
            method="PUT",
            headers={"Content-Type": object_content_type},
            key=object_key,
            expires_at=datetime.fromtimestamp(expires_unix_timestamp, tz=UTC),
            expires_in_seconds=resolved_expires_seconds,
        )

    def create_presigned_get_url(
        self,
        key: str,
        *,
        expires_in_seconds: int | None = None,
    ) -> PresignedGetUrl:
        object_key = self._validate_key(key)
        resolved_expires_seconds = self._resolve_expires_seconds(
            expires_in_seconds,
            default_expires_seconds=self._default_get_url_expires_seconds,
        )
        expires_unix_timestamp = int(time.time()) + resolved_expires_seconds
        url = self._presigned_url(
            method="GET",
            key=object_key,
            content_md5="",
            content_type="",
            expires_unix_timestamp=expires_unix_timestamp,
        )

        return PresignedGetUrl(
            url=url,
            method="GET",
            headers={},
            key=object_key,
            expires_at=datetime.fromtimestamp(expires_unix_timestamp, tz=UTC),
            expires_in_seconds=resolved_expires_seconds,
        )

    def put_object(
        self,
        key: str,
        *,
        body: bytes,
        content_type: str,
    ) -> PutObjectResult:
        object_key = self._validate_key(key)
        object_content_type = self._validate_content_type(content_type)
        content_md5 = hashlib.md5(
            body,
            usedforsecurity=False,
        ).hexdigest()
        response = self._send_ucloud_request(
            method="PUT",
            key=object_key,
            operation="put_object",
            headers={
                "Content-Type": object_content_type,
                "Content-Length": str(len(body)),
                "Content-MD5": content_md5,
            },
            body=body,
            expected_status_codes=frozenset({200}),
        )

        return PutObjectResult(
            key=object_key,
            etag=self._extract_etag(response.headers),
        )

    def get_object(self, key: str) -> StoredObject:
        object_key = self._validate_key(key)
        response = self._send_ucloud_request(
            method="GET",
            key=object_key,
            operation="get_object",
            headers={},
            body=None,
            expected_status_codes=frozenset({200}),
        )
        body = response.content

        return StoredObject(
            key=object_key,
            body=body,
            content_type=response.headers.get("Content-Type"),
            content_length=self._parse_content_length(
                response.headers.get("Content-Length")
            )
            or len(body),
            etag=self._extract_etag(response.headers),
            metadata=self._extract_user_metadata(response.headers),
        )

    def head_object(self, key: str) -> ObjectMetadata:
        object_key = self._validate_key(key)
        response = self._send_ucloud_request(
            method="HEAD",
            key=object_key,
            operation="head_object",
            headers={},
            body=None,
            expected_status_codes=frozenset({200}),
        )

        return self._object_metadata(object_key, response.headers)

    def delete_object(self, key: str) -> None:
        object_key = self._validate_key(key)
        self._send_ucloud_request(
            method="DELETE",
            key=object_key,
            operation="delete_object",
            headers={},
            body=None,
            expected_status_codes=frozenset({204}),
        )

    def _send_ucloud_request(
        self,
        *,
        method: str,
        key: str,
        operation: str,
        headers: Mapping[str, str],
        body: bytes | None,
        expected_status_codes: frozenset[int],
    ) -> httpx2.Response:
        request_headers = dict(headers)
        request_headers["Authorization"] = self._authorization_header(
            method=method,
            key=key,
            headers=request_headers,
        )

        try:
            response = self._client().request(
                method,
                self._object_url(key),
                headers=request_headers,
                content=body,
            )
        except httpx2.HTTPError as exc:
            logger.error(
                event="storage.ucloud_us3.request.failed",
                operation=operation,
                key=key,
                error_code=type(exc).__name__,
                message="UCloud US3 request failed",
            )
            raise ObjectStorageError(
                "UCloud US3 request failed",
            ) from exc

        if response.status_code not in expected_status_codes:
            self._raise_for_response(
                response,
                operation=operation,
                key=key,
            )

        logger.info(
            event="storage.ucloud_us3.request.succeeded",
            operation=operation,
            key=key,
            status_code=response.status_code,
            etag=self._extract_etag(response.headers),
            content_length=self._parse_content_length(
                response.headers.get("Content-Length")
            ),
        )
        return response

    def _raise_for_response(
        self,
        response: httpx2.Response,
        *,
        operation: str,
        key: str,
    ) -> NoReturn:
        payload = self._response_error_payload(response)
        ret_code = self._as_int(payload.get("RetCode"))
        err_msg = self._as_str(payload.get("ErrMsg")) or response.reason_phrase
        session_id = response.headers.get("X-SessionId")

        logger.warning(
            event="storage.ucloud_us3.request.rejected",
            operation=operation,
            key=key,
            status_code=response.status_code,
            ret_code=ret_code,
            err_msg=err_msg,
            session_id=session_id,
        )

        message = (
            err_msg
            or f"UCloud US3 {operation} failed with HTTP {response.status_code}"
        )
        error_class = (
            ObjectStorageNotFoundError
            if response.status_code == 404
            else ObjectStorageError
        )
        raise error_class(
            message,
        )

    def _authorization_header(
        self,
        *,
        method: str,
        key: str,
        headers: Mapping[str, str],
    ) -> str:
        string_to_sign = self._string_to_sign(
            method=method,
            key=key,
            content_md5=self._header_value(headers, "Content-MD5"),
            content_type=self._header_value(headers, "Content-Type"),
            date_or_expires=self._header_value(headers, "Date"),
            canonicalized_ucloud_headers=self._canonicalized_ucloud_headers(
                headers
            ),
        )
        return f"UCloud {self._public_key}:{self._sign_string(string_to_sign)}"

    def _presigned_url(
        self,
        *,
        method: str,
        key: str,
        content_md5: str,
        content_type: str,
        expires_unix_timestamp: int,
    ) -> str:
        signature = self._sign_presigned_url(
            method=method,
            key=key,
            content_md5=content_md5,
            content_type=content_type,
            expires_unix_timestamp=expires_unix_timestamp,
        )
        query = urlencode(
            {
                "UCloudPublicKey": self._public_key,
                "Expires": str(expires_unix_timestamp),
                "Signature": signature,
            }
        )
        return f"{self._object_url(key)}?{query}"

    def _sign_put_url(
        self,
        *,
        key: str,
        content_type: str,
        expires_unix_timestamp: int,
    ) -> str:
        return self._sign_presigned_url(
            method="PUT",
            key=key,
            content_md5="",
            content_type=content_type,
            expires_unix_timestamp=expires_unix_timestamp,
        )

    def _sign_presigned_url(
        self,
        *,
        method: str,
        key: str,
        content_md5: str,
        content_type: str,
        expires_unix_timestamp: int,
    ) -> str:
        string_to_sign = self._string_to_sign(
            method=method,
            key=key,
            content_md5=content_md5,
            content_type=content_type,
            date_or_expires=str(expires_unix_timestamp),
            canonicalized_ucloud_headers="",
        )
        return self._sign_string(string_to_sign)

    def _string_to_sign(
        self,
        *,
        method: str,
        key: str,
        content_md5: str,
        content_type: str,
        date_or_expires: str,
        canonicalized_ucloud_headers: str,
    ) -> str:
        return "\n".join(
            [
                method,
                content_md5,
                content_type,
                date_or_expires,
                (
                    canonicalized_ucloud_headers
                    + self._canonicalized_resource(key)
                ),
            ]
        )

    def _sign_string(self, string_to_sign: str) -> str:
        digest = hmac.new(
            self._private_key.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            hashlib.sha1,
        ).digest()
        return base64.b64encode(digest).decode("utf-8")

    def _object_url(self, key: str) -> str:
        scheme = "https" if self._use_https else "http"
        encoded_key = quote(key, safe="/._~-")
        return f"{scheme}://{self._bucket}{self._upload_suffix}/{encoded_key}"

    def _canonicalized_resource(self, key: str) -> str:
        return f"/{self._bucket}/{key}"

    @staticmethod
    def _canonicalized_ucloud_headers(headers: Mapping[str, str]) -> str:
        canonicalized_headers: list[tuple[str, str]] = []
        for name, value in headers.items():
            normalized_name = name.lower()
            if not normalized_name.startswith("x-ucloud-"):
                continue
            normalized_value = " ".join(value.split())
            canonicalized_headers.append(
                (normalized_name, normalized_value),
            )

        return "".join(
            f"{name}:{value}\n"
            for name, value in sorted(canonicalized_headers)
        )

    def _client(self) -> httpx2.Client:
        if self._http_client is None:
            self._http_client = httpx2.Client()
        return self._http_client

    def _object_metadata(
        self,
        key: str,
        headers: Mapping[str, str],
    ) -> ObjectMetadata:
        return ObjectMetadata(
            key=key,
            content_type=headers.get("Content-Type"),
            content_length=self._parse_content_length(
                headers.get("Content-Length")
            ),
            etag=self._extract_etag(headers),
            last_modified=self._parse_http_datetime(
                headers.get("Last-Modified")
            ),
            storage_class=headers.get("X-Ufile-Storage-Class"),
            metadata=self._extract_user_metadata(headers),
        )

    @staticmethod
    def _response_error_payload(
        response: httpx2.Response,
    ) -> Mapping[str, object]:
        try:
            payload = response.json()
        except ValueError:
            return {}

        if isinstance(payload, Mapping):
            return payload
        return {}

    @staticmethod
    def _header_value(headers: Mapping[str, str], name: str) -> str:
        normalized_name = name.lower()
        for header_name, header_value in headers.items():
            if header_name.lower() == normalized_name:
                return header_value
        return ""

    @staticmethod
    def _extract_etag(headers: Mapping[str, str]) -> str | None:
        etag = headers.get("ETag")
        if etag is None:
            return None
        normalized_etag = etag.strip().strip('"')
        return normalized_etag or None

    @staticmethod
    def _extract_user_metadata(headers: Mapping[str, str]) -> Mapping[str, str]:
        return {
            name.lower()[len(_USER_METADATA_HEADER_PREFIX) :]: value
            for name, value in headers.items()
            if name.lower().startswith(_USER_METADATA_HEADER_PREFIX)
        }

    @staticmethod
    def _parse_content_length(value: str | None) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except ValueError:
            return None

    @staticmethod
    def _parse_http_datetime(value: str | None) -> datetime | None:
        if value is None:
            return None
        try:
            parsed_value = parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return None
        if parsed_value.tzinfo is None:
            return parsed_value.replace(tzinfo=UTC)
        return parsed_value

    @staticmethod
    def _as_int(value: object) -> int | None:
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return None
        return None

    @staticmethod
    def _as_str(value: object) -> str | None:
        if isinstance(value, str):
            return value
        return None

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

    def _resolve_expires_seconds(
        self,
        expires_in_seconds: int | None,
        *,
        default_expires_seconds: int,
    ) -> int:
        return self._validate_expires_seconds(
            expires_in_seconds
            if expires_in_seconds is not None
            else default_expires_seconds
        )

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
