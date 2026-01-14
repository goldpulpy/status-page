"""Dashboard page."""

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.shared import config

router = APIRouter()


@router.get(f"/{config.admin.safe_path}")
async def dashboard_page(request: Request) -> RedirectResponse:
    """Redirect to groups page."""
    return RedirectResponse(url=f"{config.admin.safe_path}/groups")
