"""API base route."""

from fastapi import APIRouter

from . import health, middlewares
from .v1 import router as v1_router

router = APIRouter(prefix="/api")

router.include_router(v1_router)

__all__ = ["health", "middlewares", "router"]
