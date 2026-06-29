"""Application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from may_backend.api.v1.router import router as api_v1_router
from may_backend.infrastructure.supabase import close_supabase, initialize_supabase
from may_backend.logger.middleware import LogContextMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    initialize_supabase()
    try:
        yield
    finally:
        await close_supabase()


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.add_middleware(LogContextMiddleware)
    app.include_router(api_v1_router)
    return app
