"""Monitors Group models."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.database.models.group import MonitorGroupModel


class MonitorsGroupResponse(BaseModel):
    """Group status response."""

    id: UUID
    name: str
    created_at: datetime

    @classmethod
    def from_orm(cls, group: MonitorGroupModel) -> "MonitorsGroupResponse":
        """Create a MonitorsGroupResponse from a MonitorGroupModel."""
        return cls(id=group.id, name=group.name, created_at=group.created_at)


class MonitorsGroupRequest(BaseModel):
    """Create group request."""

    name: str = Field(..., max_length=255, min_length=1)


class MonitorsGroupListResponse(BaseModel):
    """List groups response."""

    groups: list[MonitorsGroupResponse]
    total: int
