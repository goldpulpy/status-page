"""Worker scheduler."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, ClassVar

from app.enums import MonitorType

if TYPE_CHECKING:
    from collections.abc import Callable

    from app.database.models.monitor import MonitorModel
    from app.monitoring.manager import WorkerManager
    from app.monitoring.workers.base import BaseWorker
    from app.repositories.uow import SqlAlchemyUnitOfWork

from app.monitoring.workers.base import WorkerConfig
from app.monitoring.workers.http import HTTPWorker

logger = logging.getLogger(__name__)


class WorkerSchedulerError(Exception):
    """Base exception for worker scheduler."""


class UnsupportedMonitorTypeError(WorkerSchedulerError):
    """Raised when monitor type is not supported."""


class WorkerScheduler:
    """Schedules when workers should run."""

    _WORKER_TYPE_MAP: ClassVar[dict[MonitorType, type[BaseWorker]]] = {
        MonitorType.HTTP: HTTPWorker,
    }

    def __init__(
        self,
        manager: WorkerManager,
        uow_factory: Callable[[], SqlAlchemyUnitOfWork],
    ) -> None:
        """Initialize worker scheduler."""
        self._manager = manager
        self._uow_factory = uow_factory

    async def initialize(self) -> None:
        """Initialize workers when app starts."""
        async with self._uow_factory() as uow:
            monitors = await uow.monitors.find_all()

        if not monitors:
            logger.debug("No monitors found to initialize")
            return

        logger.debug("Loading %s monitors", len(monitors))

        workers: list[BaseWorker] = []
        failed_count = 0

        for monitor in monitors:
            try:
                worker = self._create_worker(monitor)
                workers.append(worker)
            except Exception:
                logger.exception(
                    "Failed to create worker from monitor ID=%s",
                    monitor.id,
                )
                failed_count += 1

        if not workers:
            logger.warning(
                "No workers created from %s monitors",
                len(monitors),
            )
            return

        results = await asyncio.gather(
            *[self._manager.add_worker(w) for w in workers],
            return_exceptions=True,
        )

        success_count = sum(1 for r in results if not isinstance(r, Exception))

        logger.info(
            "Initialized %s/%s workers (failed: %s)",
            success_count,
            len(monitors),
            failed_count + len(workers) - success_count,
        )

    async def start_worker(self, monitor: MonitorModel) -> None:
        """Start worker."""
        worker = self._create_worker(monitor)
        await self._manager.add_worker(worker)

    async def stop_worker(self, monitor: MonitorModel) -> None:
        """Stop workers."""
        await self._manager.delete_worker(monitor.id)

    async def restart_worker(self, monitor: MonitorModel) -> None:
        """Restart worker."""
        try:
            await self.stop_worker(monitor)
        except Exception:
            logger.exception(
                "Failed to stop worker ID=%s, starting anyway",
                monitor.id,
            )
        finally:
            await self.start_worker(monitor)

    async def graceful_shutdown(self) -> None:
        """Gracefully shutdown workers."""
        await self._manager.graceful_shutdown()

    def _map_config(self, monitor: MonitorModel) -> WorkerConfig:
        """Map monitor to worker config."""
        return WorkerConfig(
            id=monitor.id,
            endpoint=monitor.endpoint,
            method=monitor.method,
            headers=monitor.headers,
            request_body=monitor.request_body,
            expected_response_code=monitor.expected_response_code,
            expected_content_pattern=monitor.expected_content_pattern,
            latency_threshold_ms=monitor.latency_threshold_ms or 1000,
            error_mapping=monitor.error_mapping,
        )

    def _map_worker_type(self, monitor_type: MonitorType) -> type[BaseWorker]:
        """Map monitor type to worker type."""
        worker_type = self._WORKER_TYPE_MAP.get(monitor_type)
        if worker_type is None:
            msg = f"Unsupported monitor type: {monitor_type}"
            raise UnsupportedMonitorTypeError(msg)
        return worker_type

    def _create_worker(self, monitor: MonitorModel) -> BaseWorker:
        """Create worker from monitor model."""
        worker_type = self._map_worker_type(monitor.type)
        config = self._map_config(monitor)
        return worker_type(config, self._uow_factory)
