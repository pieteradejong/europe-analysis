"""
Eurostat Statistics API client.

We use the Eurostat "Statistics API" which returns JSON-stat 2.0 by default.

Base URL (as of 2025):
  https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# HTTP Status code constants
HTTP_CLIENT_ERROR_MIN = 400
HTTP_SERVER_ERROR_MIN = 500
HTTP_TOO_MANY_REQUESTS = 429


class EurostatClient:
    """Small HTTP client wrapper with retry/backoff for Eurostat."""

    def __init__(
        self,
        base_url: str = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/",
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_backoff: float = 1.0,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.headers = headers or {
            "User-Agent": "europe-analysis (Eurostat crawler; contact: local-dev)",
            "Accept": "application/json",
        }

    def get_dataset(
        self, dataset_id: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Fetch a Eurostat dataset slice.

        Args:
            dataset_id: Eurostat dataset id (e.g., 'demo_pjan')
            params: Query params (filters). Example:
              {'geo': 'DE', 'time': '2023', 'sex': 'T', 'age': 'TOTAL'}

        Returns:
            Parsed JSON object.
        """
        url = f"{self.base_url}{dataset_id}"
        params = params or {}

        last_exc: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout, headers=self.headers) as client:
                    resp = client.get(url, params=params)
                    resp.raise_for_status()
                    result: dict[str, Any] = resp.json()
                    return result
            except (
                httpx.TimeoutException,
                httpx.RequestError,
                httpx.HTTPStatusError,
            ) as exc:
                last_exc = exc
                # Don't retry on 4xx (likely a bad query), except 429.
                if isinstance(exc, httpx.HTTPStatusError):
                    status = exc.response.status_code
                    if (
                        HTTP_CLIENT_ERROR_MIN <= status < HTTP_SERVER_ERROR_MIN
                        and status != HTTP_TOO_MANY_REQUESTS
                    ):
                        raise
                if attempt < self.max_retries:
                    sleep_s = self.retry_backoff * (2**attempt)
                    logger.warning(
                        "Eurostat request failed (attempt %d/%d), sleeping %.1fs: %s",
                        attempt + 1,
                        self.max_retries + 1,
                        sleep_s,
                        exc,
                    )
                    import time

                    time.sleep(sleep_s)
                    continue
                raise

        # Unreachable, but keeps type-checkers happy.
        raise RuntimeError(f"Eurostat request failed: {last_exc}")
