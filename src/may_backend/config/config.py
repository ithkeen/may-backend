"""Application configuration."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class _Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    log_level: LogLevel = Field(
        default="INFO",
        validation_alias="LOG_LEVEL",
    )
    log_dir: Path = Field(default=Path("logs"), validation_alias="LOG_DIR")
    log_file: str = Field(default="app.jsonl", validation_alias="LOG_FILE")
    log_retention_days: int = Field(
        default=7,
        ge=1,
        validation_alias="LOG_RETENTION_DAYS",
    )
    ucloud_us3_bucket: str = Field(
        default="",
        validation_alias="UCLOUD_US3_BUCKET",
    )
    ucloud_us3_upload_suffix: str = Field(
        default=".cn-bj.ufileos.com",
        validation_alias="UCLOUD_US3_UPLOAD_SUFFIX",
    )
    ucloud_us3_public_key: str = Field(
        default="",
        validation_alias="UCLOUD_US3_PUBLIC_KEY",
    )
    ucloud_us3_private_key: str = Field(
        default="",
        validation_alias="UCLOUD_US3_PRIVATE_KEY",
    )
    ucloud_us3_use_https: bool = Field(
        default=True,
        validation_alias="UCLOUD_US3_USE_HTTPS",
    )
    ucloud_us3_put_url_expires_seconds: int = Field(
        default=900,
        ge=60,
        le=3600,
        validation_alias="UCLOUD_US3_PUT_URL_EXPIRES_SECONDS",
    )
    ucloud_us3_get_url_expires_seconds: int = Field(
        default=900,
        ge=60,
        le=3600,
        validation_alias="UCLOUD_US3_GET_URL_EXPIRES_SECONDS",
    )

    @field_validator("log_level", mode="before")
    @classmethod
    def _normalize_log_level(cls, value: object) -> object:
        if isinstance(value, str):
            return value.upper()
        return value


@dataclass(frozen=True)
class _LogConfig:
    level: LogLevel
    log_dir: Path
    log_file: str
    retention_days: int

    @property
    def log_path(self) -> Path:
        return self.log_dir / self.log_file


@dataclass(frozen=True)
class _UCloudUS3Config:
    bucket: str
    upload_suffix: str
    public_key: str
    private_key: str
    use_https: bool
    put_url_expires_seconds: int
    get_url_expires_seconds: int


_settings = _Settings()

log_config = _LogConfig(
    level=_settings.log_level,
    log_dir=_settings.log_dir,
    log_file=_settings.log_file,
    retention_days=_settings.log_retention_days,
)
ucloud_us3_config = _UCloudUS3Config(
    bucket=_settings.ucloud_us3_bucket,
    upload_suffix=_settings.ucloud_us3_upload_suffix,
    public_key=_settings.ucloud_us3_public_key,
    private_key=_settings.ucloud_us3_private_key,
    use_https=_settings.ucloud_us3_use_https,
    put_url_expires_seconds=_settings.ucloud_us3_put_url_expires_seconds,
    get_url_expires_seconds=_settings.ucloud_us3_get_url_expires_seconds,
)
