"""Status API models."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.database.models.incident import IncidentModel
from app.database.models.monitor import MonitorModel
from app.enums import ComponentType, IncidentStatus, IncidentType


class IncidentResponse(BaseModel):
    """Incident status response."""

    id: UUID
    message: str
    type: IncidentType
    status: IncidentStatus
    created_at: datetime
    ended_at: datetime | None

    @classmethod
    def from_orm(cls, incident: IncidentModel) -> "IncidentResponse":
        """Create a IncidentResponse from a IncidentModel."""
        return cls(
            id=incident.id,
            message=incident.message,
            type=incident.type,
            status=incident.status,
            created_at=incident.created_at,
            ended_at=incident.ended_at,
        )


class StatusMonitorResponse(BaseModel):
    """Monitor status response."""

    type: ComponentType
    id: UUID
    name: str
    incidents: list[IncidentResponse]
    created_at: datetime

    @classmethod
    def from_orm(
        cls,
        monitor: MonitorModel,
        incidents: list[IncidentModel],
    ) -> "StatusMonitorResponse":
        """Create a StatusMonitorResponse from a MonitorModel."""
        return cls(
            type=ComponentType.MONITOR,
            id=monitor.id,
            name=monitor.name,
            incidents=[
                IncidentResponse.from_orm(incident) for incident in incidents
            ],
            created_at=monitor.created_at,
        )


class StatusMonitorGroupResponse(BaseModel):
    """Monitor group status response."""

    type: ComponentType
    id: UUID
    name: str
    monitors: list[StatusMonitorResponse]


class StatusResponse(BaseModel):
    """Overall status response."""

    components: list[StatusMonitorResponse | StatusMonitorGroupResponse]
    last_updated: datetime = Field(default_factory=datetime.now)
