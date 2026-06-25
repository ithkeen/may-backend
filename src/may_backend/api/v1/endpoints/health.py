"""Health check endpoints."""

from fastapi import APIRouter

from may_backend.logger import logger


router = APIRouter()


@router.get("/ping")
def ping() -> dict[str, str]:
    logger.info(event="health.ping")
    return {"message": "pong"}
