"""Authentication models."""

from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Login authentication request."""

    username: str = Field(..., max_length=255, min_length=1)
    password: str = Field(..., max_length=255, min_length=1)


class LoginResponse(BaseModel):
    """Login authentication response."""

    status: str
    message: str
    created_at: datetime
    expires_at: datetime


class LogoutResponse(BaseModel):
    """Logout authentication response."""

    status: str
    message: str
