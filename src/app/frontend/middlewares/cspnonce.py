"""CSP nonce middleware."""

import logging
import secrets
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.shared.headers import get_secure_headers
from app.shared import config

logger = logging.getLogger(__name__)


class CSPNonceMiddleware(BaseHTTPMiddleware):
    """Middleware for generating nonce."""

    NONCE_LENGTH = 16

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Dispatch middleware."""
        
        if config.app.is_development:
            return await call_next(request)

        nonce = secrets.token_urlsafe(self.NONCE_LENGTH)
        request.state.csp_nonce = nonce

        response = await call_next(request)

        content_type = response.headers.get("content-type", "").lower()
        if content_type.startswith("text/html"):
            self._apply_security_headers(response, nonce)

        return response

    def _apply_security_headers(self, response: Response, nonce: str) -> None:
        """Apply security headers."""
        secure_headers: list[tuple[str, str]] = get_secure_headers(nonce)
        for key, value in secure_headers:
            response.headers[key] = value
