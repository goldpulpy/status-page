"""Middlewares for the API."""

from fastapi import FastAPI

from .authentication import SSRAuthMiddleware
from .context import ContextMiddleware
from .cspnonce import CSPNonceMiddleware
from .minify import HTMLMinifyMiddleware


def setup_middlewares(app: FastAPI) -> None:
    """Set up middlewares."""
    app.add_middleware(CSPNonceMiddleware)
    app.add_middleware(HTMLMinifyMiddleware)
    app.add_middleware(SSRAuthMiddleware)
    app.add_middleware(ContextMiddleware)


__all__ = ["setup_middlewares"]
