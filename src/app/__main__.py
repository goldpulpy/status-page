"""Main entry point for the application."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, status
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded

from app import api, frontend, shared
from app.api import docs
from app.container import Container
from app.shared import config
from app.shared.constants import SECURE_HEADERS
from app.shared.exc_handlers import (
    not_found_handler,
    rate_limit_exception_handler,
)
from app.shared.log_filters import HealthCheckFilter

logging.getLogger("uvicorn.access").addFilter(HealthCheckFilter())
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("httpcore").setLevel(logging.ERROR)
logging.getLogger("aiosqlite").setLevel(logging.ERROR)

logging.basicConfig(
    level=config.app.log_level.value,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

container = Container()
container.wire(packages=[api, frontend, shared])


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[Any, Any]:
    """Lifespan."""
    worker_scheduler = container.worker_scheduler()
    await worker_scheduler.initialize()

    try:
        yield

    finally:
        logger.info("Shutting down the application")
        await worker_scheduler.graceful_shutdown()


app = FastAPI(
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
    openapi_url=None if config.app.is_production else "/openapi.json",
)

app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent / "frontend" / "static"),
    name="static",
)

app.add_exception_handler(status.HTTP_404_NOT_FOUND, not_found_handler)
app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)

app.add_middleware(api.middlewares.APIAuthMiddleware)
app.add_middleware(frontend.middlewares.SSRAuthMiddleware)
app.add_middleware(frontend.middlewares.HTMLMinifyMiddleware)

app.include_router(api.router)
app.include_router(api.health.router)
app.include_router(frontend.router)

if config.app.is_development:
    docs.setup_scalar(app)

if __name__ == "__main__":
    logger.info(
        "Application starting, environment: %s, log level: %s",
        config.app.environment.value,
        config.app.log_level.value,
    )
    logger.info(
        "Admin path: http://%s:%s/%s",
        config.app.host,
        config.app.port,
        config.admin.safe_path,
    )

    uvicorn.run(
        app,
        host=config.app.host,
        port=config.app.port,
        limit_concurrency=1000,
        timeout_keep_alive=5,
        timeout_graceful_shutdown=10,
        headers=SECURE_HEADERS if config.app.is_production else None,
        server_header=False if config.app.is_production else True,
    )
