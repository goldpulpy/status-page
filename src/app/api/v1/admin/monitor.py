"""Monitor CRUD endpoints."""

import logging
from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)

from app.api.models.monitor import (
    MonitorRequest,
    MonitorResponse,
    MonitorsListResponse,
    MonitorsTypesResponse,
)
from app.container import Container
from app.database.models.monitor import MonitorModel
from app.enums import MonitorType
from app.monitoring.scheduler import WorkerScheduler
from app.repositories.uow import SqlAlchemyUnitOfWork

logger = logging.getLogger(__name__)
limiter = Container.limiter()
router = APIRouter(tags=["Monitors"])


@router.get(
    "/monitors",
    status_code=status.HTTP_200_OK,
    summary="List monitors",
    description="Retrieve all available monitors",
    response_description="List of monitors",
    responses={
        200: {
            "description": "Successful response",
            "model": MonitorsListResponse,
        },
        401: {"description": "Unauthorized"},
        500: {"description": "Internal server error"},
    },
)
@inject
async def list_monitors(
    request: Request,
    uow_factory: Annotated[
        Callable[[], SqlAlchemyUnitOfWork],
        Depends(Provide[Container.uow_factory.provider]),
    ],
) -> MonitorsListResponse:
    """List all monitors."""
    async with uow_factory() as uow:
        monitors = await uow.monitors.find_all()

    logger.debug("Found %d monitors", len(monitors))

    return MonitorsListResponse(
        monitors=[MonitorResponse.from_orm(monitor) for monitor in monitors],
        total=len(monitors),
    )


@router.get(
    "/monitors/types",
    status_code=status.HTTP_200_OK,
    summary="List types of monitors",
    description="Retrieve all available types of monitors",
    response_description="List of types of monitors",
    responses={
        200: {
            "description": "Successful response",
            "model": MonitorsTypesResponse,
        },
        401: {"description": "Unauthorized"},
        500: {"description": "Internal server error"},
    },
)
async def monitor_types(request: Request) -> MonitorsTypesResponse:
    """List all types of monitors."""
    return MonitorsTypesResponse(
        types=list(MonitorType),
        total=len(MonitorType),
    )


@router.get(
    "/monitors/{monitor_id}",
    status_code=status.HTTP_200_OK,
    summary="Get monitor",
    description="Retrieve a specific monitor",
    response_description="Monitor",
    responses={
        200: {
            "description": "Successful response",
            "model": MonitorResponse,
        },
        401: {"description": "Unauthorized"},
        404: {"description": "Monitor not found"},
        500: {"description": "Internal server error"},
    },
)
@inject
async def get_monitor(
    request: Request,
    monitor_id: UUID,
    uow_factory: Annotated[
        Callable[[], SqlAlchemyUnitOfWork],
        Depends(Provide[Container.uow_factory.provider]),
    ],
) -> MonitorResponse:
    """Get a specific monitor."""
    async with uow_factory() as uow:
        monitor = await uow.monitors.find_by_id(monitor_id)

    if not monitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitor not found",
        )

    return MonitorResponse.from_orm(monitor)


@router.post(
    "/monitors",
    status_code=status.HTTP_201_CREATED,
    summary="Create monitor",
    description="Create a new monitor",
    response_description="Created monitor",
    responses={
        201: {
            "description": "Successful response",
            "model": MonitorResponse,
        },
        400: {"description": "Bad request"},
        401: {"description": "Unauthorized"},
        404: {"description": "Group not found"},
        422: {"description": "Validation error"},
        500: {"description": "Internal server error"},
    },
)
@limiter.limit("1/second")
@inject
async def create_monitor(
    request: Request,
    create_request: MonitorRequest,
    uow_factory: Annotated[
        Callable[[], SqlAlchemyUnitOfWork],
        Depends(Provide[Container.uow_factory.provider]),
    ],
    scheduler: Annotated[
        WorkerScheduler,
        Depends(Provide[Container.worker_scheduler]),
    ],
) -> MonitorResponse:
    """Create a new monitor."""
    async with uow_factory() as uow:
        if create_request.group_id:
            group = await uow.groups.find_by_id(create_request.group_id)
            if not group:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Group not found",
                )

        monitor = await uow.monitors.save(
            MonitorModel(**create_request.model_dump()),
        )

    await scheduler.start_worker(monitor)
    logger.debug("Monitor id=%s, name='%s' created", monitor.id, monitor.name)

    return MonitorResponse.from_orm(monitor)


@router.put(
    "/monitors/{monitor_id}",
    status_code=status.HTTP_200_OK,
    summary="Update monitor",
    description="Update an existing monitor",
    response_description="Updated monitor",
    responses={
        200: {
            "description": "Successful response",
            "model": MonitorResponse,
        },
        400: {"description": "Bad request"},
        401: {"description": "Unauthorized"},
        404: {"description": "Monitor or group not found"},
        422: {"description": "Validation error"},
        500: {"description": "Internal server error"},
    },
)
@limiter.limit("1/second")
@inject
async def update_monitor(
    request: Request,
    monitor_id: UUID,
    update_request: MonitorRequest,
    uow_factory: Annotated[
        Callable[[], SqlAlchemyUnitOfWork],
        Depends(Provide[Container.uow_factory.provider]),
    ],
    scheduler: Annotated[
        WorkerScheduler,
        Depends(Provide[Container.worker_scheduler]),
    ],
) -> MonitorResponse:
    """Update a specific monitor."""
    async with uow_factory() as uow:
        monitor = await uow.monitors.find_by_id(
            monitor_id,
            with_for_update=True,
        )

        if not monitor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Monitor not found",
            )

        if (
            update_request.group_id
            and monitor.group_id != update_request.group_id
        ):
            group = await uow.groups.find_by_id(update_request.group_id)
            if not group:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Group not found",
                )

        update_data = update_request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(monitor, field, value)

        monitor = await uow.monitors.save(monitor)

    await scheduler.restart_worker(monitor)
    logger.debug("Monitor id=%s, name='%s' updated", monitor.id, monitor.name)

    return MonitorResponse.from_orm(monitor)


@router.delete(
    "/monitors/{monitor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete monitor",
    description="Delete an existing monitor",
    responses={
        204: {"description": "Successful response"},
        401: {"description": "Unauthorized"},
        404: {"description": "Monitor not found"},
        500: {"description": "Internal server error"},
    },
)
@limiter.limit("1/second")
@inject
async def delete_monitor(
    request: Request,
    monitor_id: UUID,
    uow_factory: Annotated[
        Callable[[], SqlAlchemyUnitOfWork],
        Depends(Provide[Container.uow_factory.provider]),
    ],
    scheduler: Annotated[
        WorkerScheduler,
        Depends(Provide[Container.worker_scheduler]),
    ],
) -> None:
    """Delete a specific monitor."""
    async with uow_factory() as uow:
        monitor = await uow.monitors.find_by_id(
            monitor_id,
            with_for_update=True,
        )

        if not monitor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Monitor not found",
            )

        monitor.is_deleted = True
        await uow.monitors.save(monitor)

    logger.debug("Monitor id=%s, name='%s' deleted", monitor.id, monitor.name)
    await scheduler.stop_worker(monitor)
