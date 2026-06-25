"""Log file writing."""

from pathlib import Path

from may_backend.logger.archive import archive_if_needed


def append_line(path: Path, line: str, *, retention_days: int) -> None:
    archive_if_needed(path, retention_days)
    with path.open("a", encoding="utf-8") as file:
        file.write(line)
