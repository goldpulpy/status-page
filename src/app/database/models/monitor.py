"""Monitor model."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    TIMESTAMP,
    Boolean,
    Enum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy import UUID as UUIDTYPE
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.enums import MonitorType


class MonitorModel(Base):
    """Monitor model."""

    __tablename__ = "monitors"
    id: Mapped[UUID] = mapped_column(
        UUIDTYPE,
        default=uuid4,
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(String, nullable=False)

    group_id: Mapped[UUID | None] = mapped_column(
        UUIDTYPE,
        ForeignKey("groups.id"),
        nullable=True,
    )

    type: Mapped[MonitorType] = mapped_column(
        Enum(MonitorType),
        nullable=False,
    )

    endpoint: Mapped[str] = mapped_column(String, nullable=False)
    method: Mapped[str | None] = mapped_column(String, nullable=True)
    headers: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    request_body: Mapped[str | None] = mapped_column(String, nullable=True)

    expected_response_code: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    expected_content_pattern: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    latency_threshold_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    error_mapping: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=datetime.now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        onupdate=datetime.now,
        default=datetime.now,
        nullable=False,
    )
