"""Database health endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from may_backend.api.dependencies import PingDatabaseDep
from may_backend.application.use_cases.health import DatabasePingUnavailable


router = APIRouter()


class DatabasePingResponse(BaseModel):
    message: str


@router.get("/ping", response_model=DatabasePingResponse)
async def ping_database(use_case: PingDatabaseDep) -> DatabasePingResponse:
    try:
        message = await use_case.execute()
    except DatabasePingUnavailable as exc:
        raise HTTPException(
            status_code=503,
            detail="database ping unavailable",
        ) from exc

    return DatabasePingResponse(message=message)
