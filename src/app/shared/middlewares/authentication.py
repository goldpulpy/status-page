"""Authentication middleware."""

from __future__ import annotations

import logging
from abc import abstractmethod
from typing import TYPE_CHECKING

from jwt.exceptions import (
    DecodeError,
    ExpiredSignatureError,
    ImmatureSignatureError,
    InvalidIssuerError,
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

    def _verify_token(  # noqa: PLR0911
        self,
        request: Request,
    ) -> bool:
        """Verify and extract token data."""
        token = request.cookies.get("token")
        if not token:
            logger.debug("Missing token for %s", request.url.path)
            return False

        try:
            data = verify_auth_token(token)

        except ExpiredSignatureError:
            logger.debug("Token expired for path: %s", request.url.path)
            return False

        except InvalidIssuerError:
            logger.debug("Invalid token issuer for path: %s", request.url.path)
            return False

        except ImmatureSignatureError:
            logger.debug("Token not yet valid for path: %s", request.url.path)
            return False

        except (DecodeError, InvalidTokenError) as e:
            logger.debug("Token validation failed: %s", e)
            return False

        sub = data.get("sub")
        if not sub or not isinstance(sub, str):
            logger.debug(
                "Invalid or missing 'sub' claim in token for path: %s",
                request.url.path,
            )
            return False

        return True

    @abstractmethod
    def _should_authenticate(self, path: str) -> bool:
        """Check if path requires authentication."""
        raise NotImplementedError
