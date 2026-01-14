"""Admin panel base page routes."""

from fastapi import APIRouter

from app.shared import config

from . import groups, login, monitors, root

router = APIRouter()

router.include_router(root.router)

router.prefix = f"/{config.admin.safe_path}"
router.include_router(login.router)
router.include_router(monitors.router)
router.include_router(groups.router)
