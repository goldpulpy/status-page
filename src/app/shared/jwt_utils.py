"""JWT utils."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from jwt import (
    decode,
    encode,
)

from app.shared import config


def create_auth_token(sub: str) -> tuple[str, datetime, datetime]:
    """Create a JWT token.

    Returns:
        tuple[str, datetime, datetime]: JWT token, created at, expires at

    """
    created_at = datetime.now(UTC)
    expires_at = created_at + timedelta(seconds=config.jwt.expires_in)

    jwt_token = encode(
        {
            "sub": sub,
            "exp": int(expires_at.timestamp()),
            "iat": int(created_at.timestamp()),
            "nbf": int(created_at.timestamp()),
            "iss": config.jwt.issuer,
        },
        config.jwt.secret,
        algorithm=config.jwt.algorithm,
    )

    return jwt_token, created_at, expires_at


def verify_auth_token(token: str) -> dict:
    """Verify a JWT token and return its payload."""
    return decode(
        token,
        config.jwt.secret,
        algorithms=[config.jwt.algorithm],
    )
