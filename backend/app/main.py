from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import apply_schema, get_engine
from app.errors import register_exception_handlers
from app.logging import RequestIdMiddleware, setup_logging
from app.routes import artifacts, config_route, health, search, sessions

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    logger.info("app_startup")
    try:
        engine = get_engine()
        await apply_schema(engine)
    except Exception as exc:
        logger.warning("db_schema_apply_deferred", error=str(exc))
    yield
    logger.info("app_shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title="The Lenny Growth Assistant API",
        version="0.1.0",
        description="Grounded conversational assistant over 300+ Lenny's Podcast episodes.",
        lifespan=lifespan,
    )

    # Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIdMiddleware)

    # Error handling
    register_exception_handlers(app)

    # Mount API routers
    app.include_router(health.router, prefix="/api")
    app.include_router(config_route.router, prefix="/api")
    app.include_router(sessions.router, prefix="/api")
    app.include_router(artifacts.router, prefix="/api")
    app.include_router(search.router, prefix="/api")

    return app


app = create_app()
