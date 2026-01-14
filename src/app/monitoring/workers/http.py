"""HTTP worker for endpoint monitoring."""

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

from app.enums import IncidentType
from app.monitoring.workers.base import BaseWorker, Incident

logger = logging.getLogger(__name__)

HTTP_SERVER_ERROR_MIN = 500
HTTP_SERVER_ERROR_MAX = 600
HTTP_CLIENT_ERROR_MIN = 400
HTTP_CLIENT_ERROR_MAX = 499


class HTTPWorker(BaseWorker):
    """HTTP worker for monitoring endpoint."""

    async def check(self) -> None:
        """Perform endpoint health check."""
        async with httpx.AsyncClient(
            timeout=self._config.check_timeout,
        ) as client:
            try:
                response = await self._execute_request(client)
                response.raise_for_status()

                incident = self._validate_response(response)

                if incident:
                    await self.upsert_incident(incident)

                else:
                    await self.resolve_incident()

            except HTTPStatusError as e:
                await self._handle_status_code_error(e)

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

    async def _execute_request(self, client: httpx.AsyncClient) -> Response:
        """Execute HTTP request based on configuration."""
        headers = self._config.headers or {}
        method = self._config.method or "GET"

        kwargs = {}
        if self._config.request_body:
            kwargs["json"] = self._config.request_body

        response = await client.request(
            method,
            self._config.endpoint,
            headers=headers,
            **kwargs,
        )

        logger.debug(
            "HTTP check endpoint=%s, status_code=%s, latency_ms=%s completed",
            self._config.endpoint,
            response.status_code,
            int(response.elapsed.total_seconds() * 1000),
        )

        return response

    def _validate_response(self, response: Response) -> Incident | None:
        """Validate HTTP response based on configuration."""
        latency_ms = response.elapsed.total_seconds() * 1000

        if latency_ms > self._config.latency_threshold_ms:
            return Incident(
                message="High latency",
                type=IncidentType.DEGRADED,
            )

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

    async def _handle_status_code_error(self, error: HTTPStatusError) -> None:
        """Handle HTTP request errors with custom mapping."""
        logger.debug(
            "HTTP status error endpoint=%s, status_code=%s",
            self._config.endpoint,
            error.response.status_code,
        )

        status_code = error.response.status_code
        message = f"Service failed with status code {status_code}"

        if HTTP_SERVER_ERROR_MIN <= status_code < HTTP_SERVER_ERROR_MAX:
            incident_type = IncidentType.MAJOR_OUTAGE

        elif HTTP_CLIENT_ERROR_MIN <= status_code < HTTP_CLIENT_ERROR_MAX:
            incident_type = IncidentType.PARTIAL_OUTAGE

        else:
            incident_type = IncidentType.PARTIAL_OUTAGE

        if self._config.error_mapping:
            error_mapping = {
                str(k): v for k, v in self._config.error_mapping.items()
            }
            message = error_mapping.get(str(status_code), message)

        await self.upsert_incident(
            Incident(
                message=message,
                type=incident_type,
            ),
        )
