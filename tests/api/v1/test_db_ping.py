from __future__ import annotations

import anyio
from httpx2 import ASGITransport, AsyncClient

from may_backend.api import deps
from may_backend.app import create_app


class _FakeObjectStorage:
    pass


class _FakePingRepository:
    def __init__(self, message: str | None = "pong") -> None:
        self._message = message

    async def get_ping_message(self) -> str | None:
        return self._message


class _FailingPingRepository:
    async def get_ping_message(self) -> str | None:
        raise RuntimeError("database unavailable")


def _run_db_ping_request(repository: object) -> tuple[int, dict[str, object]]:
    async def run_request() -> None:
        app = create_app()
        app.dependency_overrides[deps.get_object_storage] = _FakeObjectStorage
        app.dependency_overrides[deps.get_database_ping_repository] = (
            lambda: repository
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            response = await client.get("/api/v1/db/ping")

        run_request.status_code = response.status_code
        run_request.body = response.json()

    anyio.run(run_request)
    return run_request.status_code, run_request.body


def test_db_ping_returns_pong() -> None:
    status_code, body = _run_db_ping_request(_FakePingRepository())

    assert status_code == 200
    assert body == {"message": "pong"}


def test_db_ping_returns_503_when_record_is_missing() -> None:
    status_code, body = _run_db_ping_request(_FakePingRepository(None))

    assert status_code == 503
    assert body == {"detail": "database ping unavailable"}


def test_db_ping_returns_503_when_repository_fails() -> None:
    status_code, body = _run_db_ping_request(_FailingPingRepository())

    assert status_code == 503
    assert body == {"detail": "database ping unavailable"}
