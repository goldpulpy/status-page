"""Context middleware."""

import logging

from starlette.types import ASGIApp, Receive, Scope, Send

from app.shared import config

logger = logging.getLogger(__name__)


class ContextMiddleware:
    """ASGI middleware for SSR context injection."""

    def __init__(self, app: ASGIApp) -> None:
        """Initialize context middleware."""
        self.app = app
        self._org_name = config.app.organization_name
        self._theme = config.app.theme
        self._safe_path = config.admin.safe_path
        self._admin_prefix = f"/{self._safe_path}"

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        """Process ASGI request."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        if "state" not in scope:
            scope["state"] = {}

        elif not isinstance(scope["state"], dict):
            logger.warning("Invalid state type in scope")
            scope["state"] = {}

        scope["state"]["organization_name"] = self._org_name
        scope["state"]["theme"] = self._theme

        path = scope.get("path", "")
        admin_path = self._get_admin_path(path)
        scope["state"]["admin_path"] = admin_path

        await self.app(scope, receive, send)

    def _get_admin_path(self, path: str) -> str | None:
        """Determine if request is for admin path."""
        if (
            path.startswith(self._admin_prefix + "/")
            or path == self._admin_prefix
        ):
            return self._safe_path
        return None
