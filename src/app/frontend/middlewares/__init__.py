"""Middlewares for the API."""

from .authentication import SSRAuthMiddleware
from .cspnonce import CSPNonceMiddleware
from .minify import HTMLMinifyMiddleware

__all__ = ["CSPNonceMiddleware", "HTMLMinifyMiddleware", "SSRAuthMiddleware"]
