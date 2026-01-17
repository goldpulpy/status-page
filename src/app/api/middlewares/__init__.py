"""Middlewares for the API."""

from fastapi import FastAPI

from .authentication import APIAuthMiddleware


def setup_middlewares(app: FastAPI) -> None:
    """Set up middlewares."""
    app.add_middleware(APIAuthMiddleware)


__all__ = ["setup_middlewares"]
