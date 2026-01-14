"""Frontend routers."""

from fastapi import APIRouter

from . import admin, status

router = APIRouter(tags=["Pages"], include_in_schema=False)

router.include_router(status.router)
router.include_router(admin.router)
