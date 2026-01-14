"""Middlewares for the API."""

from .authentication import APIAuthMiddleware

__all__ = ["APIAuthMiddleware"]
