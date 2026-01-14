"""Incident repository implementation."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import desc, select

from app.database.models.incident import IncidentModel
from app.enums import IncidentStatus

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class IncidentRepository:
    """Incident repository."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the incident repository."""
        self._session = session

    async def find_by_id(
        self,
        incident_id: UUID,
        *,
        with_for_update: bool = False,
    ) -> IncidentModel | None:
        """Find a incident by ID."""
        stmt = select(IncidentModel).where(IncidentModel.id == incident_id)

        if with_for_update:
            stmt = stmt.with_for_update()

        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_all(
        self,
        *,
        days: int | None = None,
    ) -> list[IncidentModel]:
        """Find all incidents."""
        stmt = select(IncidentModel).order_by(desc(IncidentModel.created_at))

        if days:
            cutoff = datetime.now(UTC) - timedelta(days=days)
            stmt = stmt.where(IncidentModel.created_at > cutoff)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def find_open(
        self,
        monitor_id: UUID,
        *,
        with_for_update: bool = False,
    ) -> IncidentModel | None:
        """Find all open incidents."""
        stmt = select(IncidentModel).where(
            IncidentModel.monitor_id == monitor_id,
            IncidentModel.status == IncidentStatus.OPEN,
        )

        if with_for_update:
            stmt = stmt.with_for_update()

        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def save(self, monitor: IncidentModel) -> IncidentModel:
        """Save a incident."""
        persistent_model = await self._session.merge(monitor)

        await self._session.flush()
        await self._session.refresh(persistent_model)

        return persistent_model
