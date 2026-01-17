"""Enums for the application."""

from enum import Enum


class Environment(str, Enum):
    """Environment enum."""

    DEVELOPMENT = "development"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """LogLevel enum."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Theme(str, Enum):
    """Theme enum."""

    DEFAULT = "default"
    MODERN = "modern"
    DARK = "dark"


class ComponentType(str, Enum):
    """Component types."""

    GROUP = "group"
    MONITOR = "monitor"


class MonitorType(str, Enum):
    """Monitor types."""

    HTTP = "HTTP"


class IncidentType(str, Enum):
    """Incident types."""

    DEGRADED = "degraded"
    PARTIAL_OUTAGE = "partial_outage"
    MAJOR_OUTAGE = "major_outage"


class IncidentStatus(str, Enum):
    """Incident status."""

    OPEN = "open"
    RESOLVED = "resolved"
