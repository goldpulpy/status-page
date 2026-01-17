"""Status page router."""

from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.container import Container
from app.shared import config

router = APIRouter()


@router.get("/")
@inject
async def status_page(
    request: Request,
    jinja: Annotated[Jinja2Templates, Depends(Provide[Container.jinja])],
) -> HTMLResponse:
    """Status page."""
    return jinja.TemplateResponse(
        "status/index.html",
        {
            "request": request,
            "theme": config.app.theme,
            "organization_name": config.app.organization_name,
        },
    )
