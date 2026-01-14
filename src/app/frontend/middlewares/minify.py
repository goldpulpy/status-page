"""Minify HTML middleware."""

import logging
import re
from collections.abc import Awaitable, Callable

import htmlmin
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, StreamingResponse
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class HTMLMinifyMiddleware(BaseHTTPMiddleware):
    """Minify HTML middleware."""

    def __init__(
        self,
        app: ASGIApp,
        max_size_bytes: int = 1024 * 1024,
    ) -> None:
        """Initialize the HTML minify middleware."""
        super().__init__(app)
        self.max_size_bytes = max_size_bytes

    def _extract_charset(self, content_type: str) -> str:
        """Extract charset from content-type header."""
        match = re.search(r"charset=([^\s;]+)", content_type, re.IGNORECASE)
        return match.group(1) if match else "utf-8"

    def _build_response(
        self,
        response: Response,
        body: bytes,
        content_type: str,
        *,
        minified: bool = False,
    ) -> Response:
        """Build a response with appropriate headers."""
        headers = dict(response.headers)
        if minified:
            for key in ("content-length", "transfer-encoding", "etag"):
                headers.pop(key, None)

        headers["Content-Length"] = str(len(body))

        return Response(
            content=body,
            status_code=response.status_code,
            headers=headers,
            media_type=content_type,
        )

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Dispatch middleware."""
        response = await call_next(request)

        if not 200 <= response.status_code < 300:  # noqa: PLR2004
            return response

        content_type = response.headers.get("content-type", "")

        if not content_type.startswith("text/html") or isinstance(
            response,
            StreamingResponse,
        ):
            return response

        chunks = []
        total_size = 0
        size_exceeded = False

        async for chunk in response.body_iterator:  # type: ignore[attr-defined]
            chunks.append(chunk)
            total_size += len(chunk)

            if total_size > self.max_size_bytes:
                size_exceeded = True
                logger.warning(
                    "HTML response too large for minification (%d > %d): "
                    "%d bytes",
                    total_size,
                    self.max_size_bytes,
                    total_size,
                )
                break

        body = b"".join(chunks)

        if not body or size_exceeded:
            return self._build_response(
                response,
                body,
                content_type,
                minified=False,
            )

        charset = self._extract_charset(content_type)
        minified_bytes = body

        try:
            decoded = body.decode(charset)
            minified = htmlmin.minify(
                decoded,
                remove_comments=True,
                remove_empty_space=True,
            )
            minified_bytes = minified.encode(charset)

            logger.debug(
                "HTML minification for %s: %d -> %d bytes (saved %.2f%%)",
                request.url.path,
                len(body),
                len(minified_bytes),
                ((len(body) - len(minified_bytes)) / len(body)) * 100,
            )

        except (UnicodeDecodeError, LookupError):
            logger.exception("Failed to decode HTML with charset: %s", charset)
            minified_bytes = body

        except Exception:
            logger.exception("HTML minification failed")
            minified_bytes = body

        return self._build_response(
            response,
            minified_bytes,
            content_type,
            minified=bool(minified_bytes != body),
        )
