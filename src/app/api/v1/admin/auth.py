"""Login endpoints."""

import hmac
import logging

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    Response,
    status,
)

from app.api.models.authentication import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
)
from app.container import Container
from app.shared import config
from app.shared.jwt_utils import create_auth_token

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Authentication"])
limiter = Container.limiter()


def set_auth_cookie(response: Response, token: str) -> None:
    """Set authentication cookie with proper security settings."""
    response.set_cookie(
        key=config.cookie.key,
        value=token,
        httponly=True,
        samesite="lax",
        secure=config.app.https,
        max_age=config.jwt.expires_in,
    )


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    summary="Admin authentication",
    description="Authenticate via admin credentials",
    response_description="Admin authentication response",
    responses={
        200: {
            "description": "Admin authenticated successfully",
            "model": LoginResponse,
        },
        400: {"description": "Missing required fields"},
        401: {"description": "Invalid credentials"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"},
    },
)
@limiter.limit("5/minute")
async def login(
    request: Request,
    response: Response,
    login_request: LoginRequest,
) -> LoginResponse:
    """Admin authentication."""
    if not (
        hmac.compare_digest(
            login_request.username.encode(),
            config.admin.username.encode(),
        )
        and hmac.compare_digest(
            login_request.password.encode(),
            config.admin.password.encode(),
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    jwt_token, created_at, expires_at = create_auth_token(
        config.admin.username,
    )

    logger.debug(
        "Created JWT token (sub=%s, exp=%s, iat=%s, iss=%s)",
        config.admin.username,
        expires_at,
        created_at,
        config.jwt.issuer,
    )

    set_auth_cookie(response, jwt_token)

    return LoginResponse(
        status="success",
        message="User authentication successful",
        created_at=created_at,
        expires_at=expires_at,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Admin logout",
    description="Logout via admin credentials",
    response_description="User logout response",
    responses={
        200: {
            "description": "Admin logged out successfully",
            "model": LogoutResponse,
        },
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"},
    },
)
@limiter.limit("1/second")
async def logout(
    request: Request,
    response: Response,
) -> LogoutResponse:
    """Admin logout."""
    response.delete_cookie(
        key="token",
        httponly=True,
        samesite="none" if config.app.is_production else "lax",
        secure=config.app.is_production,
    )

    return LogoutResponse(
        status="success",
        message="Logged out successfully",
    )
