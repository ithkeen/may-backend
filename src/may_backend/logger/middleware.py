"""Logger middleware."""

from collections.abc import Awaitable, Callable, Iterable, MutableMapping
from typing import cast
from uuid import uuid4

from may_backend.logger.context import log_context


Scope = MutableMapping[str, object]
Message = MutableMapping[str, object]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]


class LogContextMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        headers = _headers(scope)
        trace_id = headers.get("x-trace-id") or _new_trace_id()
        request_id = headers.get("x-request-id") or _new_request_id()

        with log_context(trace_id=trace_id, request_id=request_id):
            await self.app(scope, receive, send)


def _headers(scope: Scope) -> dict[str, str]:
    values: dict[str, str] = {}
    headers = cast(Iterable[tuple[bytes, bytes]], scope.get("headers", ()))
    for key, value in headers:
        values[key.decode("latin-1").lower()] = value.decode("latin-1")
    return values


def _new_trace_id() -> str:
    return f"trc_{uuid4().hex}"


def _new_request_id() -> str:
    return f"req_{uuid4().hex}"
