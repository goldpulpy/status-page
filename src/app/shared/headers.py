"""Server headers."""

from typing import Final

from app.shared import config

STATIC_SECURITY_HEADERS: Final[list[tuple[str, str]]] = [
    ("X-Content-Type-Options", "nosniff"),
    ("X-Frame-Options", "DENY"),
    ("Referrer-Policy", "strict-origin-when-cross-origin"),
    ("Permissions-Policy", "geolocation=(), microphone=(), camera=()"),
]


def _build_csp_policy(nonce: str) -> str:
    """Build CSP policy string."""
    directives = [
        "default-src 'self'",
        f"script-src 'self' 'nonce-{nonce}' 'unsafe-eval'",  # unsafe-eval: Alpine.js requirement # noqa: E501
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data: https:",
        "font-src 'self'",
        "connect-src 'self'",
        "manifest-src 'self'",
        "worker-src 'self'",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
    ]

    if config.app.https:
        directives.append("upgrade-insecure-requests")

    return "; ".join(directives) + ";"


def get_secure_headers(nonce: str) -> list[tuple[str, str]]:
    """Get secure headers with CSP nonce."""
    headers = list(STATIC_SECURITY_HEADERS)
    headers.append(("Content-Security-Policy", _build_csp_policy(nonce)))

    if config.app.https:
        headers.append(
            (
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains; preload",
            ),
        )

    return headers
