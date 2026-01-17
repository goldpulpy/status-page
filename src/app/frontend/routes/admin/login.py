"""Authentication page."""

from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.container import Container

router = APIRouter()


@router.get("/login")
@inject
async def login_page(
    request: Request,
    jinja: Annotated[Jinja2Templates, Depends(Provide[Container.jinja])],
) -> HTMLResponse:
    """Get login page."""
    return jinja.TemplateResponse("admin/login.html", {"request": request})
