"""Log archive support."""

from datetime import datetime, timedelta
from pathlib import Path


def archive_if_needed(log_path: Path, retention_days: int) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    _archive_current_log_if_from_previous_day(log_path)
    _delete_expired_archives(log_path, retention_days)


def _archive_current_log_if_from_previous_day(log_path: Path) -> None:
    if not log_path.exists():
        return

    modified_at = datetime.fromtimestamp(log_path.stat().st_mtime)
    if modified_at.date() == datetime.now().date():
        return

    log_path.rename(_next_archive_path(log_path, modified_at))


def _next_archive_path(log_path: Path, archived_at: datetime) -> Path:
    timestamp = archived_at.strftime("%Y%m%d-%H%M%S")
    archive_path = log_path.with_name(f"{log_path.stem}-{timestamp}{log_path.suffix}")

    counter = 1
    while archive_path.exists():
        archive_path = log_path.with_name(
            f"{log_path.stem}-{timestamp}-{counter}{log_path.suffix}"
        )
        counter += 1

    return archive_path


def _delete_expired_archives(log_path: Path, retention_days: int) -> None:
    cutoff = datetime.now() - timedelta(days=retention_days)
    pattern = f"{log_path.stem}-*{log_path.suffix}"

    for archive_path in log_path.parent.glob(pattern):
        archive_time = _archive_time_from_name(log_path, archive_path)
        if archive_time is not None and archive_time < cutoff:
            archive_path.unlink(missing_ok=True)


def _archive_time_from_name(log_path: Path, archive_path: Path) -> datetime | None:
    prefix = f"{log_path.stem}-"
    suffix = log_path.suffix

    if not archive_path.name.startswith(prefix) or not archive_path.name.endswith(suffix):
        return None

    timestamp = archive_path.name[len(prefix) : -len(suffix)]
    timestamp = timestamp.split("-", maxsplit=2)
    if len(timestamp) < 2:
        return None

    try:
        return datetime.strptime("-".join(timestamp[:2]), "%Y%m%d-%H%M%S")
    except ValueError:
        return None
