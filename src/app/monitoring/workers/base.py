"""Base worker class."""

import asyncio
import contextlib
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.database.models.incident import IncidentModel
from app.enums import IncidentStatus, IncidentType
from app.repositories.uow import SqlAlchemyUnitOfWork

logger = logging.getLogger(__name__)


class WorkerConfig(BaseModel):
    """Worker config."""

    id: UUID
    interval: int = Field(default=60, gt=0)
    initial_delay: int = Field(default=0, ge=0)
    check_timeout: int = Field(default=30, gt=0)

    endpoint: str
    latency_threshold_ms: int
    method: str | None = None
    headers: dict[str, str] | None = None
    request_body: str | None = None
    expected_response_code: int | None = None
    expected_content_pattern: str | None = None
    error_mapping: dict[str | int, str] | None = None


class Incident(BaseModel):
    """Incident model."""

    message: str
    type: IncidentType


class BaseWorker(ABC):
    """Base worker class."""

    def __init__(
        self,
        config: WorkerConfig,
        uow_factory: Callable[[], SqlAlchemyUnitOfWork],
    ) -> None:
        """Initialize worker."""
        self._config = config
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()
        self._uow_factory = uow_factory
        self._lock = asyncio.Lock()

    @abstractmethod
    async def check(self) -> None:
        """Check endpoint."""
        raise NotImplementedError

    @property
    def is_running(self) -> bool:
        """Check if worker is running."""
        return self._task is not None and not self._task.done()

    @property
    def config(self) -> WorkerConfig:
        """Get worker config."""
        return self._config

    async def upsert_incident(self, incident: Incident) -> None:
        """Create or update incident."""
        async with self._uow_factory() as uow:
            open_incident = await uow.incidents.find_open(
                self._config.id,
                with_for_update=True,
            )

            if not open_incident:
                incident_model = self._build_incident_model(incident, None)
                await uow.incidents.save(incident_model)
                return

            is_same_incident = (
                incident.message == open_incident.message
                and incident.type == open_incident.type
            )

            if not is_same_incident:
                await self._resolve_incident(uow, open_incident)
                incident_model = self._build_incident_model(incident, None)

            else:
                incident_model = self._build_incident_model(
                    incident,
                    open_incident.id,
                )

            await uow.incidents.save(incident_model)

    async def resolve_incident(self) -> None:
        """Resolve incident."""
        async with self._uow_factory() as uow:
            open_incident = await uow.incidents.find_open(
                self._config.id,
                with_for_update=True,
            )

            if open_incident:
                await self._resolve_incident(uow, open_incident)

                logger.debug("Incident ID=%s resolved", open_incident.id)

    async def start(self) -> None:
        """Start worker."""
        async with self._lock:
            if self.is_running:
                logger.warning(
                    "Worker ID=%s is already running",
                    self._config.id,
                )
                return

            self._stop_event.clear()
            self._task = asyncio.create_task(self._run())

            logger.debug("Worker ID=%s started", self._config.id)

    async def stop(self, stop_timeout: float | None = None) -> None:
        """Stop worker gracefully."""
        async with self._lock:
            if not self.is_running:
                logger.warning("Worker ID=%s is not running", self._config.id)
                return

            logger.debug("Stopping worker ID=%s", self._config.id)
            self._stop_event.set()

            if self._task is not None:
                try:
                    await asyncio.wait_for(self._task, timeout=stop_timeout)

                except TimeoutError:
                    logger.warning(
                        "Worker ID=%s did not stop in time, cancelling",
                        self._config.id,
                    )
                    self._task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await self._task

            self._task = None
            logger.debug("Worker ID=%s stopped", self._config.id)

    async def _run(self) -> None:
        """Run the main loop for checking."""
        try:
            if self._config.initial_delay > 0:
                await asyncio.sleep(self._config.initial_delay)

            while not self._stop_event.is_set():
                try:
                    async with asyncio.timeout(self._config.check_timeout):
                        await self.check()

                except Exception:
                    logger.exception(
                        "Error in worker cycle for ID=%s",
                        self._config.id,
                    )

                with contextlib.suppress(asyncio.TimeoutError):
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=self._config.interval,
                    )

        except asyncio.CancelledError:
            logger.debug("Worker ID=%s cancelled", self._config.id)
            raise

    def _build_incident_model(
        self,
        incident: Incident,
        incident_id: UUID | None,
    ) -> IncidentModel:
        """Build incident model."""
        return IncidentModel(
            id=incident_id,
            monitor_id=self._config.id,
            message=incident.message,
            type=incident.type,
        )

    async def _resolve_incident(
        self,
        uow: SqlAlchemyUnitOfWork,
        open_incident: IncidentModel,
    ) -> None:
        """Change incident status to resolved."""
        open_incident.status = IncidentStatus.RESOLVED
        open_incident.ended_at = datetime.now(UTC)

        await uow.incidents.save(open_incident)
