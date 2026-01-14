"""Frontend package."""

from . import middlewares
from .routes import router

__all__ = ["middlewares", "router"]
