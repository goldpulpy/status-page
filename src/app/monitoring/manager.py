"""Worker manager."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from app.monitoring.workers.base import BaseWorker

logger = logging.getLogger(__name__)


class WorkerManager:
    """Worker manager."""

    def __init__(self) -> None:
        """Initialize the worker manager."""
        self._workers: dict[UUID, BaseWorker] = {}
        self._lock = asyncio.Lock()

    async def add_worker(self, worker: BaseWorker) -> None:
        """Add a worker."""
        async with self._lock:
            if worker.config.id in self._workers:
                logger.warning(
                    "Worker ID=%s already exists, skipping",
                    worker.config.id,
                )
                return

            try:
                await worker.start()
                self._workers[worker.config.id] = worker

            except Exception:
                logger.exception(
                    "Failed to start worker: %s",
                    worker.config.id,
                )

                try:
                    await worker.stop()

                except Exception:
                    logger.exception(
                        "Failed to stop worker during cleanup: %s",
                        worker.config.id,
                    )

                raise

        logger.debug("Worker ID=%s added to manager", worker.config.id)

    async def delete_worker(self, worker_id: UUID) -> None:
        """Delete worker."""
        async with self._lock:
            worker = self._workers.pop(worker_id, None)

        if worker:
            try:
                await worker.stop()

            except Exception:
                logger.exception("Failed to stop worker %s", worker.config.id)
                raise

        logger.debug("Worker ID=%s removed from manager", worker_id)

    async def graceful_shutdown(self, stop_timeout: float = 30.0) -> None:
        """Stop all workers with timeout."""
        logger.info("Shutting down workers=%s", len(self._workers))

        async with self._lock:
            workers = list(self._workers.values())
            self._workers.clear()

        try:
            results = await asyncio.wait_for(
                asyncio.gather(
                    *(worker.stop() for worker in workers),
                    return_exceptions=True,
                ),
                timeout=stop_timeout,
            )

        except TimeoutError:
            logger.exception(
                "Shutdown timeout exceeded, some workers may not have stopped",
            )
            return

        for worker, result in zip(workers, results, strict=True):
            if isinstance(result, Exception):
                logger.error(
                    "Failed to stop worker %s: %s",
                    worker.config.id,
                    result,
                )
