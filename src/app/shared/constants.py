"""Constants for the application."""

SECURE_HEADERS = [
    ("X-Content-Type-Options", "nosniff"),
    ("X-Frame-Options", "DENY"),
    (
        "Content-Security-Policy",
        (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none'; "
            "upgrade-insecure-requests;"
        ),
    ),
    ("Referrer-Policy", "strict-origin-when-cross-origin"),
    ("Permissions-Policy", "geolocation=(), microphone=(), camera=()"),
]
