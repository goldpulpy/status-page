"""HTTP monitor validators."""

from urllib.parse import urlparse

from fastapi import HTTPException


def _validate_endpoint(endpoint: str) -> None:
    """Validate HTTP method."""
    try:
        parsed = urlparse(endpoint)

        if parsed.scheme not in ["http", "https"]:
            raise HTTPException(status_code=400, detail="Invalid URL scheme")

        if not parsed.netloc:
            raise HTTPException(
                status_code=400,
                detail="Invalid endpoint: missing domain",
            )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail="Invalid endpoint URL format",
        ) from e


def _validate_method(method: str) -> None:
    """Validate HTTP method."""
    allowed_methods = ["GET", "POST", "PUT", "DELETE"]
    if method.upper() not in allowed_methods:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid HTTP method. Allowed: {', '.join(allowed_methods)}",
            ),
        )


def validate_http_monitor(values: dict) -> None:
    """Validate HTTP monitor configuration."""
    endpoint = values.get("endpoint")
    method = values.get("method")

    if not endpoint:
        raise HTTPException(
            status_code=400,
            detail="Missing endpoint for HTTP monitor",
        )

    if not method:
        raise HTTPException(
            status_code=400,
            detail="Missing method for HTTP monitor",
        )

    _validate_endpoint(endpoint)
    _validate_method(method)
