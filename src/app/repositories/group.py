"""Monitor group repository implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import desc, select

from app.database.models.group import MonitorGroupModel

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession


class MonitorGroupRepository:
    """Monitor group repository."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the monitor group repository."""
        self._session = session

    async def find_by_id(
        self,
        group_id: UUID,
        *,
        with_for_update: bool = False,
    ) -> MonitorGroupModel | None:
        """Find a monitor by ID."""
        stmt = select(MonitorGroupModel).where(
            MonitorGroupModel.id == group_id,
            MonitorGroupModel.is_deleted == False,  # noqa: E712
        )

        if with_for_update:
            stmt = stmt.with_for_update()

        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_all(self) -> list[MonitorGroupModel]:
        """Find all monitors."""
        result = await self._session.execute(
            select(MonitorGroupModel)
            .where(
                MonitorGroupModel.is_deleted == False,  # noqa: E712
            )
            .order_by(desc(MonitorGroupModel.created_at)),
        )
        return list(result.scalars().all())

    async def save(self, monitor: MonitorGroupModel) -> MonitorGroupModel:
        """Save a monitor."""
        persistent_model = await self._session.merge(monitor)

        await self._session.flush()
        await self._session.refresh(persistent_model)

        return persistent_model
