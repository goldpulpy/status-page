"""Authentication middleware for SSR."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ClassVar

from fastapi.responses import RedirectResponse

from app.shared import config
from app.shared.middlewares import BaseAuthMiddleware

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from fastapi import Request, Response

logger = logging.getLogger(__name__)


class SSRAuthMiddleware(BaseAuthMiddleware):
    """SSR authentication with redirect."""

    AUTH_INCLUDE_PATHS: ClassVar[set[str]] = {
        f"/{config.admin.safe_path}",
    }
    AUTH_EXCLUDE_PATHS: ClassVar[set[str]] = {
        f"/{config.admin.safe_path}/login",
    }

    def _should_authenticate(self, path: str) -> bool:
        """Check if path requires authentication."""
        if any(path.startswith(p) for p in self.AUTH_EXCLUDE_PATHS):
            return False

        return any(path.startswith(p) for p in self.AUTH_INCLUDE_PATHS)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Dispatch middleware."""
        if request.method == "OPTIONS":
            return await call_next(request)

        if not self._should_authenticate(request.url.path):
            return await call_next(request)

        if not self._verify_token(request):
            return RedirectResponse(
                url=f"/{config.admin.safe_path}/login",
                status_code=302,
            )

        return await call_next(request)
