"""Slowapi utilities."""

from __future__ import annotations

import ipaddress
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import Request

logger = logging.getLogger(__name__)


def normalize_ip(ip_str: str) -> str | None:
    """Normalize IP address."""
    try:
        addr = ipaddress.ip_address(ip_str.strip())
    except ValueError:
        return None

    if addr.is_unspecified:
        return None

    return addr.compressed


def rate_limit_func(request: Request) -> str:
    """Extract client marker for rate limiting."""
    headers = request.headers
    if cf_ip := headers.get("CF-Connecting-IP"):  # noqa: SIM102
        if ip := normalize_ip(cf_ip):
            logger.debug("Using Cloudflare IP: %s", ip)
            return ip

    if xff := headers.get("X-Forwarded-For"):
        ips = [normalize_ip(ip.strip()) for ip in xff.split(",")]
        valid_ips = [ip for ip in ips if ip]
        if valid_ips:
            logger.debug("Using X-Forwarded-For IP: %s", valid_ips[-1])
            return valid_ips[-1]

    if x_real_ip := headers.get("X-Real-IP"):  # noqa: SIM102
        if ip := normalize_ip(x_real_ip):
            logger.debug("Using X-Real-IP IP: %s", ip)
            return ip

    if client_ip := getattr(request.client, "host", None):  # noqa: SIM102
        if ip := normalize_ip(client_ip):
            logger.debug("Using client IP: %s", ip)
            return ip

    logger.warning("Could not extract valid IP")
    return f"unknown_{hash(frozenset(headers.items())) % 1000000}"
