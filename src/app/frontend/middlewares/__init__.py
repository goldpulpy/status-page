"""Middlewares for the API."""

from .authentication import SSRAuthMiddleware
from .minify import HTMLMinifyMiddleware

__all__ = ["HTMLMinifyMiddleware", "SSRAuthMiddleware"]
