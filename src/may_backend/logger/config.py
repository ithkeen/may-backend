"""Logger configuration."""

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class LoggerConfig:
    level: str
    log_dir: Path
    log_file: str
    retention_days: int

    @property
    def log_path(self) -> Path:
        return self.log_dir / self.log_file


def load_config() -> LoggerConfig:
    return LoggerConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        log_dir=Path(os.getenv("LOG_DIR", "logs")),
        log_file=os.getenv("LOG_FILE", "app.jsonl"),
        retention_days=int(os.getenv("LOG_RETENTION_DAYS", "7")),
    )
