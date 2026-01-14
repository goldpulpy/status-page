"""Logging filters."""

import logging


class HealthCheckFilter(logging.Filter):
    """Filter out health check requests from logs."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter out health check requests from logs."""
        message = record.getMessage()
        return not ("/health" in message and "GET" in message)
