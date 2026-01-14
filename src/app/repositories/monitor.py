"""Monitor repository implementation."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy import desc, select

from app.database.models.monitor import MonitorModel

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class MonitorRepository:
    """Monitor repository."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the monitor repository."""
        self._session = session

    async def find_by_id(
        self,
        monitor_id: UUID,
        *,
        with_for_update: bool = False,
    ) -> MonitorModel | None:
        """Find a monitor by ID."""
        stmt = select(MonitorModel).where(
            MonitorModel.id == monitor_id,
            MonitorModel.is_deleted == False,  # noqa: E712
        )

        if with_for_update:
            stmt = stmt.with_for_update()

        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_group_id(self, group_id: UUID) -> list[MonitorModel]:
        """Find monitors by group ID."""
        result = await self._session.execute(
            select(MonitorModel)
            .where(
                MonitorModel.group_id == group_id,
                MonitorModel.is_deleted == False,  # noqa: E712
            )
            .order_by(desc(MonitorModel.created_at)),
        )
        return list(result.scalars().all())

    async def find_all(self) -> list[MonitorModel]:
        """Find all monitors."""
        result = await self._session.execute(
            select(MonitorModel)
            .where(
                MonitorModel.is_deleted == False,  # noqa: E712
            )
            .order_by(desc(MonitorModel.created_at)),
        )
        return list(result.scalars().all())

    async def save(self, monitor: MonitorModel) -> MonitorModel:
        """Save a monitor."""
        persistent_model = await self._session.merge(monitor)

        await self._session.flush()
        await self._session.refresh(persistent_model)

        return persistent_model
