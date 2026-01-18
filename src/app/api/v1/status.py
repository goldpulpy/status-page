"""Status API."""

import logging
from collections import defaultdict
from collections.abc import Callable
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Request, status

from app.api.models.status import (
    StatusMonitorGroupResponse,
    StatusMonitorResponse,
    StatusResponse,
)
from app.container import Container
from app.database.models.group import MonitorGroupModel
from app.database.models.incident import IncidentModel
from app.database.models.monitor import MonitorModel
from app.enums import ComponentType
from app.repositories.uow import SqlAlchemyUnitOfWork

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Status"])
INCIDENT_HISTORY_DAYS = 30


def _group_by_attribute(items: list, attr_name: str) -> dict:
    """Group items by attribute."""
    result = defaultdict(list)
    for item in items:
        result[getattr(item, attr_name)].append(item)
    return dict(result)


def _build_components(
    monitors: list[MonitorModel],
    groups: list[MonitorGroupModel],
    incidents: list[IncidentModel],
) -> list[StatusMonitorGroupResponse | StatusMonitorResponse]:
    """Build list of components from monitors, groups and incidents."""
    components = []

    monitors_by_group = _group_by_attribute(monitors, "group_id")
    incidents_by_monitor = _group_by_attribute(incidents, "monitor_id")

    for group in groups:
        group_monitors = monitors_by_group.get(group.id, [])
        components.append(
            StatusMonitorGroupResponse(
                type=ComponentType.GROUP,
                id=group.id,
                name=group.name,
                monitors=[
                    StatusMonitorResponse.from_orm(
                        monitor,
                        incidents_by_monitor.get(monitor.id, []),
                    )
                    for monitor in group_monitors
                ],
            ),
        )

    orphan_monitors = monitors_by_group.get(None, [])

    components += [
        StatusMonitorResponse.from_orm(
            monitor,
            incidents_by_monitor.get(monitor.id, []),
        )
        for monitor in orphan_monitors
    ]

    return components


@router.get(
    "/status",
    status_code=status.HTTP_200_OK,
    summary="Get current monitors",
    description="Retrieve the monitors",
    response_description="Monitors status",
    responses={
        200: {
            "description": "Successful response",
            "model": StatusResponse,
        },
        500: {"description": "Internal server error"},
    },
)
@inject
async def get_status(
    request: Request,
    uow_factory: Annotated[
        Callable[[], SqlAlchemyUnitOfWork],
        Depends(Provide[Container.uow_factory.provider]),
    ],
) -> StatusResponse:
    """Get current monitors status."""
    async with uow_factory() as uow:
        monitors = await uow.monitors.find_all()
        groups = await uow.groups.find_all()
        incidents = await uow.incidents.find_all(
            last_days=INCIDENT_HISTORY_DAYS,
        )

    logger.debug(
        "Found monitors=%d, groups=%d, incidents=%d",
        len(monitors),
        len(groups),
        len(incidents),
    )

    components = _build_components(monitors, groups, incidents)

    return StatusResponse(components=components)
