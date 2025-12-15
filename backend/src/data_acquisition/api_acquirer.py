"""
API Data Acquirer

This module provides functionality for acquiring demographic data from HTTP APIs.
Includes rate limiting and retry logic.
"""

import asyncio
import logging
import time
from typing import Any

import httpx

from .base import AcquisitionResult, DataAcquirer

logger = logging.getLogger(__name__)


class APIAcquirer(DataAcquirer):
    """
    Acquires data from HTTP APIs with rate limiting and retry logic.

    Supports:
    - GET requests with query parameters
    - Rate limiting to respect API limits
    - Automatic retries on failures
    - JSON response parsing
    """

    def __init__(
        self,
        source: str,
        rate_limit: float = 1.0,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        data_path: str | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize API acquirer.

        Args:
            source: API endpoint URL
            rate_limit: Minimum seconds between requests (default: 1.0)
            timeout: Request timeout in seconds (default: 30.0)
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay: Delay between retries in seconds (default: 1.0)
            headers: HTTP headers to include in requests
            params: Query parameters for GET requests
            data_path: JSONPath-like path to data array in response
            **kwargs: Additional parameters
        """
        super().__init__(source, **kwargs)
        self.rate_limit = rate_limit
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.headers = headers or {}
        self.params = params or {}
        self.data_path = data_path
        self._last_request_time = 0.0

    def validate_source(self) -> bool:
        """
        Validate that the API URL is well-formed.

        Returns:
            True if URL is valid, False otherwise
        """
        if not self.source.startswith(("http://", "https://")):
            self.logger.error("Invalid API URL (must start with http:// or https://): %s", self.source)
            return False
        return True

    def _extract_data_path(self, data: dict[str, Any] | list[Any]) -> list[dict[str, Any]]:
        """
        Extract data array from JSON response using data_path or auto-detection.

        Args:
            data: Parsed JSON response

        Returns:
            List of dictionaries representing records
        """
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]

        if not isinstance(data, dict):
            return []

        # If data_path is specified, follow it
        if self.data_path:
            current = data
            for key in self.data_path.split("."):
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    self.logger.warning(
                        "Data path '%s' not found in response, trying auto-detection",
                        self.data_path,
                    )
                    break
            else:
                if isinstance(current, list):
                    return [item for item in current if isinstance(item, dict)]
                if isinstance(current, dict):
                    return [current]

        # Auto-detect common patterns
        for key in ["data", "items", "results", "records", "values", "features"]:
            if key in data:
                value = data[key]
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, dict)]
                if isinstance(value, dict):
                    return [value]

        # If it's a single object, wrap it in a list
        if isinstance(data, dict):
            return [data]

        return []

    def _enforce_rate_limit(self) -> None:
        """Enforce rate limiting by waiting if necessary."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < self.rate_limit:
            sleep_time = self.rate_limit - time_since_last
            self.logger.debug("Rate limiting: sleeping for %.2f seconds", sleep_time)
            time.sleep(sleep_time)
        self._last_request_time = time.time()

    def acquire(self) -> AcquisitionResult:
        """
        Acquire data from API endpoint.

        Returns:
            AcquisitionResult containing the API data as list of dictionaries
        """
        if not self.validate_source():
            return AcquisitionResult(
                success=False,
                error=f"Invalid API source: {self.source}",
            )

        # Enforce rate limiting
        self._enforce_rate_limit()

        metadata: dict[str, Any] = {
            "url": self.source,
            "rate_limit": self.rate_limit,
            "timeout": self.timeout,
            "params": self.params,
            "data_path": self.data_path,
        }

        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout, headers=self.headers) as client:
                    response = client.get(self.source, params=self.params)
                    response.raise_for_status()

                    # Parse JSON response
                    try:
                        json_data = response.json()
                    except ValueError as e:
                        error_msg = f"Invalid JSON response from API: {self.source} - {e}"
                        self.logger.error(error_msg)
                        return AcquisitionResult(success=False, error=error_msg)

                    metadata["status_code"] = response.status_code
                    metadata["response_headers"] = dict(response.headers)

                    # Extract data array
                    data = self._extract_data_path(json_data)

                    if not data:
                        return AcquisitionResult(
                            success=False,
                            error=f"No data found in API response: {self.source}. "
                            "Expected array or object with data array.",
                        )

                    metadata["records_extracted"] = len(data)
                    if data:
                        metadata["sample_keys"] = list(data[0].keys())

                    self.logger.info(
                        "Successfully acquired %d records from API: %s",
                        len(data),
                        self.source,
                    )

                    return AcquisitionResult(
                        success=True,
                        data=data,
                        metadata=metadata,
                        records_count=len(data),
                    )

            except httpx.HTTPStatusError as e:
                last_error = e
                error_msg = f"HTTP error {e.response.status_code} from API: {self.source}"
                self.logger.warning("%s (attempt %d/%d)", error_msg, attempt + 1, self.max_retries + 1)

                # Don't retry on client errors (4xx)
                if 400 <= e.response.status_code < 500:
                    return AcquisitionResult(success=False, error=error_msg)

            except httpx.TimeoutException as e:
                last_error = e
                error_msg = f"Timeout connecting to API: {self.source}"
                self.logger.warning("%s (attempt %d/%d)", error_msg, attempt + 1, self.max_retries + 1)

            except httpx.RequestError as e:
                last_error = e
                error_msg = f"Request error connecting to API: {self.source} - {e}"
                self.logger.warning("%s (attempt %d/%d)", error_msg, attempt + 1, self.max_retries + 1)

            except Exception as e:
                last_error = e
                error_msg = f"Unexpected error calling API: {self.source} - {e}"
                self.logger.error(error_msg, exc_info=True)
                # Don't retry on unexpected errors
                return AcquisitionResult(success=False, error=error_msg)

            # Wait before retry (except on last attempt)
            if attempt < self.max_retries:
                time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff

        # All retries exhausted
        final_error = f"Failed to acquire data from API after {self.max_retries + 1} attempts: {self.source}"
        if last_error:
            final_error += f" - {last_error}"
        self.logger.error(final_error)
        return AcquisitionResult(success=False, error=final_error)

