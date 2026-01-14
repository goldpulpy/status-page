"""Enums for the application."""

from enum import Enum


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
