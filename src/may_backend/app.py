"""Application factory."""

from fastapi import FastAPI

from may_backend.api.v1.router import router as api_v1_router
from may_backend.logger.middleware import LogContextMiddleware


def create_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(LogContextMiddleware)
    app.include_router(api_v1_router)
    return app
