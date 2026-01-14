"""Incident model."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import TIMESTAMP, Enum, ForeignKey, String
from sqlalchemy import UUID as UUIDTYPE
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.enums import IncidentStatus, IncidentType


class IncidentModel(Base):
    """Incident model."""

    __tablename__ = "incidents"
    id: Mapped[UUID] = mapped_column(
        UUIDTYPE,
        default=uuid4,
        primary_key=True,
    )

    monitor_id: Mapped[UUID] = mapped_column(
        UUIDTYPE,
        ForeignKey("monitors.id"),
        nullable=False,
    )

    type: Mapped[IncidentType] = mapped_column(
        Enum(IncidentType),
        nullable=False,
    )
    status: Mapped[IncidentStatus] = mapped_column(
        Enum(IncidentStatus),
        default=IncidentStatus.OPEN,
        nullable=False,
    )
    message: Mapped[str] = mapped_column(String, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=datetime.now,
        nullable=False,
    )

    ended_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )
