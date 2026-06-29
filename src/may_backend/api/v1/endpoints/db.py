"""Database health endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from may_backend.api.deps import ApplicationServicesDep
from may_backend.application.use_cases import DatabasePingUnavailable


router = APIRouter()


class DatabasePingResponse(BaseModel):
    message: str


@router.get("/ping", response_model=DatabasePingResponse)
async def ping_database(services: ApplicationServicesDep) -> DatabasePingResponse:
    try:
        message = await services.ping_database.execute()
    except DatabasePingUnavailable as exc:
        raise HTTPException(
            status_code=503,
            detail="database ping unavailable",
        ) from exc

    return DatabasePingResponse(message=message)
