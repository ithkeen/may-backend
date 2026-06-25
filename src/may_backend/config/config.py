"""Application configuration."""

from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class _LogConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        validation_alias="LOG_LEVEL",
    )
    log_dir: Path = Field(default=Path("logs"), validation_alias="LOG_DIR")
    log_file: str = Field(default="app.jsonl", validation_alias="LOG_FILE")
    retention_days: int = Field(
        default=7,
        ge=1,
        validation_alias="LOG_RETENTION_DAYS",
    )

    @field_validator("level", mode="before")
    @classmethod
    def _normalize_level(cls, value: object) -> object:
        if isinstance(value, str):
            return value.upper()
        return value

    @property
    def log_path(self) -> Path:
        return self.log_dir / self.log_file


log_config = _LogConfig()
