"""Admin panel base API route."""

from fastapi import APIRouter

from app.shared import config

from . import auth, group, monitor

router = APIRouter(prefix=f"/{config.admin.safe_path}")

router.include_router(auth.router)
router.include_router(monitor.router)
router.include_router(group.router)
