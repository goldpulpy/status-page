"""Frontend handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from dependency_injector.wiring import Provide, inject
from fastapi import Request, Response, status
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from slowapi.errors import RateLimitExceeded

from app.container import Container

if TYPE_CHECKING:
    from fastapi.templating import Jinja2Templates


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
            status_code=429,
            content={
                "error": "Too many requests",
                "detail": f"Rate limit exceeded: {exc.detail}",
            },
        )

    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )
