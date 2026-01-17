"""Context middleware."""

import logging
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.shared import config

logger = logging.getLogger(__name__)


class ContextMiddleware(BaseHTTPMiddleware):
    """Middleware for SSR context."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Dispatch middleware."""
        request.state.organization_name = config.app.organization_name
        request.state.theme = config.app.theme.value

        if request.url.path.startswith(f"/{config.admin.safe_path}"):
            request.state.admin_path = config.admin.safe_path

        return await call_next(request)

