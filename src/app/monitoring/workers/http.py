"""HTTP worker for endpoint monitoring."""

import json
import logging

import httpx
from httpx import (
    ConnectError,
    HTTPStatusError,
    PoolTimeout,
    Response,
    TimeoutException,
    TooManyRedirects,
)
from tenacity import (
    AsyncRetrying,
    before_sleep_log,
    retry_if_exception,
    stop_after_attempt,
    wait_fixed,
)

from app.enums import IncidentType
from app.monitoring.workers.base import BaseWorker, Incident

logger = logging.getLogger(__name__)

_HTTP_SERVER_ERROR_RANGE = range(500, 600)
_HTTP_CLIENT_ERROR_RANGE = range(400, 500)


def _is_retriable(exc: BaseException) -> bool:
    """Return True for transient errors that are worth retrying."""
    if isinstance(exc, HTTPStatusError):
        return exc.response.status_code not in _HTTP_CLIENT_ERROR_RANGE

    return isinstance(exc, (ConnectError, TimeoutException, PoolTimeout))


class HTTPWorker(BaseWorker):
    """HTTP worker for monitoring endpoint."""

    async def check(self) -> None:
        """Perform endpoint health check."""
        async with httpx.AsyncClient(
            timeout=self._config.check_timeout,
        ) as client:
            try:
                response = await self._request_with_retry(client)

            except HTTPStatusError as exc:
                await self._handle_status_error(exc)

            except PoolTimeout:
                await self.upsert_incident(
                    Incident(
                        message="Connection pool exhausted",
                        type=IncidentType.MAJOR_OUTAGE,
                    ),
                )

            except ConnectError:
                await self.upsert_incident(
                    Incident(
                        message="Connection error",
                        type=IncidentType.MAJOR_OUTAGE,
                    ),
                )

            except TimeoutException:
                await self.upsert_incident(
                    Incident(
                        message="Service timeout",
                        type=IncidentType.MAJOR_OUTAGE,
                    ),
                )
            except TooManyRedirects:
                await self.upsert_incident(
                    Incident(
                        message="Too many redirects",
                        type=IncidentType.PARTIAL_OUTAGE,
                    ),
                )

            except Exception:
                logger.exception(
                    "Unexpected error in worker ID=%s",
                    self._config.id,
                )
                await self.upsert_incident(
                    Incident(
                        message="Service unavailable",
                        type=IncidentType.MAJOR_OUTAGE,
                    ),
                )

            else:
                incident = self._validate_response(response)
                if incident:
                    await self.upsert_incident(incident)

                else:
                    await self.resolve_incident()

    async def _request_with_retry(self, client: httpx.AsyncClient) -> Response:
        """Execute request with retry logic."""
        retryer = AsyncRetrying(
            stop=stop_after_attempt(self._config.retry_max_attempts),
            wait=wait_fixed(self._config.retry_delay_seconds),
            retry=retry_if_exception(_is_retriable),
            reraise=True,
            before_sleep=before_sleep_log(logger, logging.DEBUG),
        )

        response: Response | None = None

        async for attempt in retryer:
            with attempt:
                response = await self._execute_request(client)
                response.raise_for_status()

        if response is None:
            msg = (
                "No HTTP response was received after retry loop - "
                f"check max attempts for worker ID={self._config.id}"
            )
            raise RuntimeError(
                msg,
            )

        return response

    async def _execute_request(self, client: httpx.AsyncClient) -> Response:
        """Execute HTTP request based on configuration."""
        method = self._config.method or "GET"
        headers = self._config.headers or {}
        kwargs: dict = {}

        if self._config.request_body:
            try:
                kwargs["json"] = json.loads(self._config.request_body)

            except json.JSONDecodeError:
                kwargs["data"] = self._config.request_body

        response = await client.request(
            method,
            self._config.endpoint,
            headers=headers,
            **kwargs,
        )

        logger.debug(
            "HTTP check completed - endpoint=%s status=%s latency=%dms",
            self._config.endpoint,
            response.status_code,
            int(response.elapsed.total_seconds() * 1000),
        )

        return response

    def _validate_response(self, response: Response) -> Incident | None:
        """Return an Incident if the response fails any configured checks."""
        latency_ms = response.elapsed.total_seconds() * 1000

        if latency_ms > self._config.latency_threshold_ms:
            return Incident(message="High latency", type=IncidentType.DEGRADED)

        if (
            self._config.expected_response_code
            and response.status_code != self._config.expected_response_code
        ):
            return Incident(
                message="Unexpected status code",
                type=IncidentType.PARTIAL_OUTAGE,
            )

        if (
            self._config.expected_content_pattern
            and self._config.expected_content_pattern not in response.text
        ):
            return Incident(
                message="Unexpected response content",
                type=IncidentType.PARTIAL_OUTAGE,
            )

        return None

    async def _handle_status_error(self, error: HTTPStatusError) -> None:
        """Map an HTTP status error to the appropriate incident type."""
        status_code = error.response.status_code

        logger.debug(
            "HTTP status error - endpoint=%s status=%s",
            self._config.endpoint,
            status_code,
        )

        if status_code in _HTTP_SERVER_ERROR_RANGE:
            incident_type = IncidentType.MAJOR_OUTAGE

        else:
            incident_type = IncidentType.PARTIAL_OUTAGE

        message = f"Service failed with status code {status_code}"
        if self._config.error_mapping:
            message = {
                str(k): v for k, v in self._config.error_mapping.items()
            }.get(str(status_code), message)

        await self.upsert_incident(
            Incident(message=message, type=incident_type),
        )
