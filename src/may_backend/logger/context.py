"""Logger context management."""

from contextlib import contextmanager
from contextvars import ContextVar
from collections.abc import Iterator


_trace_id: ContextVar[str | None] = ContextVar("trace_id", default=None)
_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_trace_id() -> str | None:
    return _trace_id.get()


def get_request_id() -> str | None:
    return _request_id.get()


@contextmanager
def log_context(
    *,
    trace_id: str | None = None,
    request_id: str | None = None,
) -> Iterator[None]:
    trace_token = _trace_id.set(trace_id)
    request_token = _request_id.set(request_id)
    try:
        yield
    finally:
        _request_id.reset(request_token)
        _trace_id.reset(trace_token)
