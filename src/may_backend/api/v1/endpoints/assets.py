"""Asset upload endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from may_backend.api.deps import ApplicationServicesDep
from may_backend.logger import logger


router = APIRouter()


class CreatePresignedPutUrlRequest(BaseModel):
    key: str
    content_type: str
    expires_in_seconds: int | None = None


class CreatePresignedPutUrlResponse(BaseModel):
    url: str
    method: Literal["PUT"]
    headers: dict[str, str]
    key: str
    expires_at: datetime
    expires_in_seconds: int


class CreateImageGenerationRequest(BaseModel):
    image_key: str
    prompt: str = Field(min_length=1, max_length=4000)

    @field_validator("prompt", mode="before")
    @classmethod
    def _normalize_prompt(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class CreateImageGenerationResponse(BaseModel):
    status: Literal["accepted"]
    image_key: str
    prompt: str


@router.post("/presigned-put-url", response_model=CreatePresignedPutUrlResponse)
def create_presigned_put_url(
    request: CreatePresignedPutUrlRequest,
    services: ApplicationServicesDep,
) -> CreatePresignedPutUrlResponse:
    try:
        presigned_url = services.create_presigned_put_url.execute(
            key=request.key,
            content_type=request.content_type,
            expires_in_seconds=request.expires_in_seconds,
        )
    except ValueError as exc:
        logger.warning(
            event="asset.presigned_put_url.rejected",
            key=request.key,
            content_type=request.content_type,
            requested_expires_in_seconds=request.expires_in_seconds,
            reason=str(exc),
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(
            event="asset.presigned_put_url.failed",
            key=request.key,
            content_type=request.content_type,
            requested_expires_in_seconds=request.expires_in_seconds,
            error_code=type(exc).__name__,
            message="failed to create presigned put url",
        )
        raise

    logger.info(
        event="asset.presigned_put_url.created",
        key=presigned_url.key,
        content_type=request.content_type,
        expires_in_seconds=presigned_url.expires_in_seconds,
    )

    return CreatePresignedPutUrlResponse(
        url=presigned_url.url,
        method=presigned_url.method,
        headers=dict(presigned_url.headers),
        key=presigned_url.key,
        expires_at=presigned_url.expires_at,
        expires_in_seconds=presigned_url.expires_in_seconds,
    )


@router.post(
    "/image-generation",
    response_model=CreateImageGenerationResponse,
)
def create_image_generation(
    request: CreateImageGenerationRequest,
) -> CreateImageGenerationResponse:
    logger.info(
        event="asset.image_generation.received",
        image_key=request.image_key,
        prompt_length=len(request.prompt),
    )

    return CreateImageGenerationResponse(
        status="accepted",
        image_key=request.image_key,
        prompt=request.prompt,
    )
