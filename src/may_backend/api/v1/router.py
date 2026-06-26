"""API v1 router."""

from fastapi import APIRouter

from may_backend.api.v1.endpoints import assets, health


router = APIRouter(prefix="/api/v1")
router.include_router(assets.router, prefix="/assets", tags=["assets"])
router.include_router(health.router)
