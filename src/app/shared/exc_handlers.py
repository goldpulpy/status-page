"""Exception handlers."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from dependency_injector.wiring import Provide, inject
from fastapi import Request, Response, status
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import IntegrityError

from app.container import Container
from app.monitoring.scheduler import (
    UnsupportedMonitorTypeError,
)

if TYPE_CHECKING:
    from fastapi.templating import Jinja2Templates

logger = logging.getLogger(__name__)


@inject
async def not_found_handler(
    request: Request,
    exc: Exception,
    jinja: Jinja2Templates = Provide[Container.jinja],
) -> HTMLResponse | JSONResponse:
    """Global 404 handler for API and web pages."""
    path = request.url.path

    if not path.startswith("/api"):
        return jinja.TemplateResponse(
            "404.html",
            {"request": request},
            status_code=status.HTTP_404_NOT_FOUND,
        )

    detail = exc.detail if isinstance(exc, HTTPException) else "Not found"

    return JSONResponse(
        content={"detail": detail},
        status_code=status.HTTP_404_NOT_FOUND,
    )


async def rate_limit_exception_handler(
    _: Request,
    exc: Exception,
) -> Response:
    """Rate limit handler."""
    if isinstance(exc, RateLimitExceeded):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "Too many requests",
                "detail": f"Rate limit exceeded: {exc.detail}",
            },
        )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error"},
    )


async def integrity_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle database integrity errors (unique constraints, foreign keys)."""
    if not isinstance(exc, IntegrityError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "Bad request",
                "detail": "Database constraint violation",
            },
        )

    error_msg = str(exc.orig) if hasattr(exc, "orig") else str(exc)

    logger.warning(
        "Database integrity error on %s: %s",
        request.url.path,
        error_msg,
    )

    if "unique" in error_msg.lower() or "duplicate" in error_msg.lower():
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": "Conflict",
                "detail": "A resource with this name already exists",
            },
        )

    if "foreign key" in error_msg.lower():
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "Bad request",
                "detail": "Referenced resource does not exist",
            },
        )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Bad request",
            "detail": "Database constraint violation",
        },
    )


async def sqlalchemy_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle general SQLAlchemy errors."""
    logger.exception(
        "Database error on %s: %s",
        request.url.path,
        exc,
    )

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": "Service unavailable",
            "detail": "Database error occurred",
        },
    )


async def worker_scheduler_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle worker scheduler errors."""
    logger.exception(
        "Worker scheduler error on %s: %s",
        request.url.path,
        exc,
    )

    if isinstance(exc, UnsupportedMonitorTypeError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "Bad request",
                "detail": f"Unsupported monitor type: {exc}",
            },
        )

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": "Service unavailable",
            "detail": "Monitoring service error occurred",
        },
    )


async def general_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle unhandled exceptions."""
    logger.exception(
        "Unhandled exception on %s: %s",
        request.url.path,
        exc,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred",
        },
    )
