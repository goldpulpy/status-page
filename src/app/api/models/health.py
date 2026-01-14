"""Health check models."""

from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    timestamp: int = Field(..., description="Timestamp")
