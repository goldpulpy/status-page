"""Status API models."""

from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.api.models.validators.http import validate_http_monitor
from app.database.models.monitor import MonitorModel
from app.enums import MonitorType


class MonitorResponse(BaseModel):
    """Monitor response."""

    id: UUID
    name: str
    group_id: UUID | None
    type: MonitorType
    endpoint: str
    method: str | None
    headers: dict | None
    request_body: str | None
    expected_response_code: int | None
    expected_content_pattern: str | None
    latency_threshold_ms: int | None
    error_mapping: dict | None

    @classmethod
    def from_orm(cls, monitor: MonitorModel) -> "MonitorResponse":
        """Create a MonitorResponse from a MonitorModel."""
        return cls(
            id=monitor.id,
            name=monitor.name,
            group_id=monitor.group_id,
            type=monitor.type,
            endpoint=monitor.endpoint,
            method=monitor.method,
            headers=monitor.headers,
            request_body=monitor.request_body,
            expected_response_code=monitor.expected_response_code,
            expected_content_pattern=monitor.expected_content_pattern,
            latency_threshold_ms=monitor.latency_threshold_ms,
            error_mapping=monitor.error_mapping,
        )


class MonitorRequest(BaseModel):
    """Monitor request."""

    name: str = Field(..., max_length=255, min_length=1)
    group_id: UUID | None = Field(...)
    type: MonitorType = Field(...)
    method: str | None = Field(...)
    endpoint: str = Field(..., max_length=255, min_length=1)
    headers: dict | None = Field(...)
    request_body: str | None = Field(...)
    expected_response_code: int | None = Field(
        ...,
    )
    expected_content_pattern: str | None = Field(...)
    latency_threshold_ms: int | None = Field(...)
    error_mapping: dict | None = Field(...)

    @model_validator(mode="before")
    @classmethod
    def validate(cls, values: dict) -> dict:
        """Validate HTTP endpoint."""
        monitor_type = values.get("type")

        if monitor_type == MonitorType.HTTP:
            validate_http_monitor(values)

        return values


class MonitorsListResponse(BaseModel):
    """List monitors response."""

    monitors: list[MonitorResponse]
    total: int


class MonitorsTypesResponse(BaseModel):
    """List types of monitors."""

    types: list[MonitorType]
    total: int
