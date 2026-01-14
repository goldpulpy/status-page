"""v1 base route."""

from fastapi import APIRouter

from . import admin, status

router = APIRouter(prefix="/v1")

router.include_router(status.router)
router.include_router(admin.router)
