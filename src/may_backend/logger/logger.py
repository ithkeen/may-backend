"""Logger facade."""

from collections.abc import Mapping
from contextlib import AbstractContextManager
from datetime import datetime, timezone
from uuid import uuid4

from may_backend.config import log_config
from may_backend.logger.context import get_request_id, get_trace_id, log_context
from may_backend.logger.formatter import format_json_line
from may_backend.logger.writer import append_line


LEVELS = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
}


def _utc_timestamp() -> str:
    value = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
    return value.replace("+00:00", "Z")


def _new_trace_id() -> str:
    return f"trc_{uuid4().hex}"


def _new_request_id() -> str:
    return f"req_{uuid4().hex}"


class Logger:
    def debug(self, **fields: object) -> None:
        self._log("DEBUG", fields)

    def info(self, **fields: object) -> None:
        self._log("INFO", fields)

    def warning(self, **fields: object) -> None:
        self._log("WARNING", fields)

    def error(self, **fields: object) -> None:
        self._log("ERROR", fields)

    def critical(self, **fields: object) -> None:
        self._log("CRITICAL", fields)

    def context(
        self,
        *,
        trace_id: str | None = None,
        request_id: str | None = None,
    ) -> AbstractContextManager[None]:
        return log_context(trace_id=trace_id, request_id=request_id)

    def _log(self, level: str, fields: Mapping[str, object]) -> None:
        try:
            config = log_config
            if LEVELS[level] < LEVELS.get(config.level, LEVELS["INFO"]):
                return

            record = {
                "timestamp": _utc_timestamp(),
                "level": level,
                "trace_id": get_trace_id() or _new_trace_id(),
                "request_id": get_request_id() or _new_request_id(),
                **fields,
            }
            append_line(
                config.log_path,
                format_json_line(record),
                retention_days=config.retention_days,
            )
        except Exception:
            return


logger = Logger()
