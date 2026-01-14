"""Health check endpoint."""

import logging
from datetime import UTC, datetime
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.models.health import HealthCheckResponse
from app.container import Container
from app.services.health.db import DatabaseHealthCheckService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Health"])
limiter = Container.limiter()


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
    summary="Health check endpoint",
    description="Check the health of the service",
    response_description="Health check response",
    responses={
        200: {
            "description": "Service is healthy",
            "model": HealthCheckResponse,
        },
        429: {"description": "Rate limit exceeded"},
        503: {"description": "Service unavailable"},
    },
)
@limiter.limit("1/second")
@inject
async def health_check(
    request: Request,
    db_health: Annotated[
        DatabaseHealthCheckService,
        Depends(Provide[Container.database_health]),
    ],
) -> HealthCheckResponse:
    """Health check endpoint."""
    db_is_healthy = await db_health.check_connection()

    if not db_is_healthy:
        logger.error("Health check failed - database connection unavailable")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection is not healthy",
        )

    return HealthCheckResponse(
        status="ok",
        timestamp=int(datetime.now(UTC).timestamp()),
    )
