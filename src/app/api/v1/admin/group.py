"""Group CRUD endpoints."""

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

from app.api.models.group import (
    MonitorsGroupListResponse,
    MonitorsGroupRequest,
    MonitorsGroupResponse,
)
from app.container import Container
from app.database.models.group import MonitorGroupModel
from app.repositories.uow import SqlAlchemyUnitOfWork

logger = logging.getLogger(__name__)
limiter = Container.limiter()
router = APIRouter(tags=["Monitor Groups"])


@router.get(
    "/groups",
    status_code=status.HTTP_200_OK,
    summary="List monitors groups",
    description="Retrieve all available monitors groups",
    response_description="List of monitors groups",
    responses={
        200: {
            "description": "Successful response",
            "model": MonitorsGroupListResponse,
        },
        401: {"description": "Unauthorized"},
        500: {"description": "Internal server error"},
    },
)
@inject
async def list_groups(
    request: Request,
    uow_factory: Annotated[
        Callable[[], SqlAlchemyUnitOfWork],
        Depends(Provide[Container.uow_factory.provider]),
    ],
) -> MonitorsGroupListResponse:
    """List all groups."""
    async with uow_factory() as uow:
        groups = await uow.groups.find_all()

    logger.debug("Found %d groups", len(groups))

    return MonitorsGroupListResponse(
        groups=[MonitorsGroupResponse.from_orm(group) for group in groups],
        total=len(groups),
    )


@router.get(
    "/groups/{group_id}",
    status_code=status.HTTP_200_OK,
    summary="Get monitors group",
    description="Retrieve a specific monitors group",
    response_description="Monitors group",
    responses={
        200: {
            "description": "Successful response",
            "model": MonitorsGroupResponse,
        },
        401: {"description": "Unauthorized"},
        404: {"description": "Group not found"},
        500: {"description": "Internal server error"},
    },
)
@inject
async def get_group(
    request: Request,
    group_id: UUID,
    uow_factory: Annotated[
        Callable[[], SqlAlchemyUnitOfWork],
        Depends(Provide[Container.uow_factory.provider]),
    ],
) -> MonitorsGroupResponse:
    """Get a specific group."""
    async with uow_factory() as uow:
        group = await uow.groups.find_by_id(group_id)

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    return MonitorsGroupResponse.from_orm(group)


@router.post(
    "/groups",
    status_code=status.HTTP_201_CREATED,
    summary="Create a monitors group",
    description="Create a new monitors group",
    response_description="Created monitors group",
    responses={
        201: {
            "description": "Successful response",
            "model": MonitorsGroupResponse,
        },
        400: {"description": "Bad request"},
        401: {"description": "Unauthorized"},
        422: {"description": "Validation error"},
        500: {"description": "Internal server error"},
    },
)
@limiter.limit("1/second")
@inject
async def create_group(
    request: Request,
    create_request: MonitorsGroupRequest,
    uow_factory: Annotated[
        Callable[[], SqlAlchemyUnitOfWork],
        Depends(Provide[Container.uow_factory.provider]),
    ],
) -> MonitorsGroupResponse:
    """Create a specific group."""
    async with uow_factory() as uow:
        group = await uow.groups.save(
            MonitorGroupModel(name=create_request.name),
        )

    logger.debug("Group id=%s, name='%s' created", group.id, group.name)

    return MonitorsGroupResponse.from_orm(group)


@router.put(
    "/groups/{group_id}",
    status_code=status.HTTP_200_OK,
    summary="Update monitors group",
    description="Update an existing monitors group",
    response_description="Updated monitors group",
    responses={
        200: {
            "description": "Successful response",
            "model": MonitorsGroupResponse,
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
async def update_group(
    request: Request,
    group_id: UUID,
    update_request: MonitorsGroupRequest,
    uow_factory: Annotated[
        Callable[[], SqlAlchemyUnitOfWork],
        Depends(Provide[Container.uow_factory.provider]),
    ],
) -> MonitorsGroupResponse:
    """Update a specific group."""
    async with uow_factory() as uow:
        group = await uow.groups.find_by_id(group_id, with_for_update=True)

        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found",
            )

        group.name = update_request.name
        group = await uow.groups.save(group)

    logger.debug(
        "Group id=%s, name='%s' updated",
        group.id,
        group.name,
    )

    return MonitorsGroupResponse.from_orm(group)


@router.delete(
    "/groups/{group_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete monitors group",
    description="Delete an existing monitors group",
    responses={
        204: {"description": "Successful response"},
        401: {"description": "Unauthorized"},
        404: {"description": "Group not found"},
        500: {"description": "Internal server error"},
    },
)
@limiter.limit("1/second")
@inject
async def delete_group(
    request: Request,
    group_id: UUID,
    uow_factory: Annotated[
        Callable[[], SqlAlchemyUnitOfWork],
        Depends(Provide[Container.uow_factory.provider]),
    ],
) -> None:
    """Delete a specific group."""
    async with uow_factory() as uow:
        group = await uow.groups.find_by_id(group_id, with_for_update=True)

        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found",
            )

        group.is_deleted = True
        await uow.groups.save(group)

    logger.debug("Group id=%s, name='%s' deleted", group.id, group.name)
