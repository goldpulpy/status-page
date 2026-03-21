"""HTTP monitor validators."""

from urllib.parse import urlparse

from fastapi import HTTPException, status

HTTP_ERROR_MIN = 100
HTTP_ERROR_MAX = 599


def _validate_endpoint(endpoint: str) -> None:
    """Validate HTTP method."""
    try:
        parsed = urlparse(endpoint)

        if parsed.scheme not in ["http", "https"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid URL scheme",
            )

        if not parsed.netloc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid endpoint: missing domain",
            )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid endpoint URL format",
        ) from e


def _validate_method(method: str) -> None:
    """Validate HTTP method."""
    allowed_methods = ["GET", "POST", "PUT", "DELETE"]
    if method.upper() not in allowed_methods:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid HTTP method. Allowed: {', '.join(allowed_methods)}",
            ),
        )


def validate_codes(values: dict) -> None:
    """Validate HTTP codes."""
    expected_response_code = values.get("expected_response_code")
    if expected_response_code is not None and not (
        HTTP_ERROR_MIN <= expected_response_code <= HTTP_ERROR_MAX
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="expected_response_code must be between 100 and 599",
        )

    latency_threshold_ms = values.get("latency_threshold_ms")
    if latency_threshold_ms is not None and latency_threshold_ms <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="latency_threshold_ms must be greater than 0",
        )

    error_mapping = values.get("error_mapping")
    if error_mapping:
        invalid_codes = []

        for code in error_mapping:
            try:
                code_int = int(code)

            except (TypeError, ValueError):
                invalid_codes.append(code)
                continue

            if code_int < HTTP_ERROR_MIN or code_int > HTTP_ERROR_MAX:
                invalid_codes.append(code)

        if invalid_codes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "error_mapping keys must be HTTP status codes between"
                    f" 100 and 599; invalid: {invalid_codes}"
                ),
            )


def validate_http_monitor(values: dict) -> None:
    """Validate HTTP monitor configuration."""
    endpoint = values.get("endpoint")
    method = values.get("method")

    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing endpoint for HTTP monitor",
        )

    if not method:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing method for HTTP monitor",
        )

    _validate_endpoint(endpoint)
    _validate_method(method)
    validate_codes(values)
