"""Authentication middleware."""

from __future__ import annotations

import logging
from abc import abstractmethod
from typing import TYPE_CHECKING

from jwt.exceptions import (
    DecodeError,
    ExpiredSignatureError,
    InvalidTokenError,
)
from starlette.middleware.base import BaseHTTPMiddleware

from app.shared.jwt_utils import verify_auth_token

if TYPE_CHECKING:
    from fastapi import Request
    from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class BaseAuthMiddleware(BaseHTTPMiddleware):
    """Base authentication middleware."""

    def __init__(self, app: ASGIApp) -> None:
        """Initialize authentication middleware."""
        super().__init__(app)

    def _verify_token(self, request: Request) -> bool:
        """Verify and extract token data."""
        token = request.cookies.get("token")
        if not token:
            logger.debug("Missing token for %s", request.url.path)
            return False

        try:
            data = verify_auth_token(token)
        except (ExpiredSignatureError, DecodeError, InvalidTokenError) as e:
            logger.debug("Token validation failed: %s", e)
            return False

        sub = data.get("sub")
        if not sub or not isinstance(sub, str):
            logger.debug("Invalid or missing user_id in token for path: %s")
            return False

        return True

    @abstractmethod
    def _should_authenticate(self, path: str) -> bool:
        """Check if path requires authentication."""
        raise NotImplementedError
