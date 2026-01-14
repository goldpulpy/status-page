"""Monitor group model."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import TIMESTAMP, Boolean, String
from sqlalchemy import UUID as UUIDTYPE
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class MonitorGroupModel(Base):
    """Monitorgroups model."""

    __tablename__ = "groups"
    id: Mapped[UUID] = mapped_column(
        UUIDTYPE,
        default=uuid4,
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(String, nullable=False)

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
