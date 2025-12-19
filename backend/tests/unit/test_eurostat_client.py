"""Tests for Eurostat HTTP client."""

from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest

from backend.src.data_acquisition.eurostat.client import EurostatClient


class TestEurostatClient:
    """Tests for EurostatClient."""

    def test_init_default_values(self) -> None:
        """Test client initialization with default values."""
        client = EurostatClient()

        assert (
            client.base_url
            == "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
        )
        assert client.timeout == 30.0
        assert client.max_retries == 3
        assert client.retry_backoff == 1.0
        assert "User-Agent" in client.headers

    def test_init_custom_values(self) -> None:
        """Test client initialization with custom values."""
        client = EurostatClient(
            base_url="https://custom.api.com/data",
            timeout=60.0,
            max_retries=5,
            retry_backoff=2.0,
            headers={"Custom-Header": "value"},
        )

        assert client.base_url == "https://custom.api.com/data/"
        assert client.timeout == 60.0
        assert client.max_retries == 5
        assert client.retry_backoff == 2.0
        assert client.headers["Custom-Header"] == "value"

    def test_base_url_trailing_slash(self) -> None:
        """Test that base_url always ends with trailing slash."""
        client1 = EurostatClient(base_url="https://api.com/data")
        client2 = EurostatClient(base_url="https://api.com/data/")

        assert client1.base_url == "https://api.com/data/"
        assert client2.base_url == "https://api.com/data/"

    @patch("backend.src.data_acquisition.eurostat.client.httpx.Client")
    def test_get_dataset_success(
        self,
        mock_httpx_client: MagicMock,
        mock_eurostat_jsonstat_response: dict[str, Any],
    ) -> None:
        """Test successful dataset retrieval."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.json.return_value = mock_eurostat_jsonstat_response
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)
        mock_httpx_client.return_value = mock_client_instance

        client = EurostatClient()
        result = client.get_dataset("demo_pjan", params={"geo": "DE"})

        assert result == mock_eurostat_jsonstat_response
        mock_client_instance.get.assert_called_once()

    @patch("backend.src.data_acquisition.eurostat.client.httpx.Client")
    def test_get_dataset_with_params(self, mock_httpx_client: MagicMock) -> None:
        """Test dataset retrieval with query parameters."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": "test"}
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)
        mock_httpx_client.return_value = mock_client_instance

        client = EurostatClient()
        params = {"geo": "DE", "time": "2023", "sex": "T"}
        client.get_dataset("demo_pjan", params=params)

        # Verify params were passed
        call_args = mock_client_instance.get.call_args
        assert call_args.kwargs["params"] == params

    @patch("backend.src.data_acquisition.eurostat.client.httpx.Client")
    def test_get_dataset_url_construction(self, mock_httpx_client: MagicMock) -> None:
        """Test that URL is constructed correctly."""
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)
        mock_httpx_client.return_value = mock_client_instance

        client = EurostatClient(base_url="https://api.com/data/")
        client.get_dataset("demo_pjan")

        call_args = mock_client_instance.get.call_args
        assert call_args.args[0] == "https://api.com/data/demo_pjan"

    @patch("time.sleep")
    @patch("backend.src.data_acquisition.eurostat.client.httpx.Client")
    def test_retry_on_timeout(
        self, mock_httpx_client: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """Test retry behavior on timeout."""
        mock_client_instance = MagicMock()
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)

        # First two calls timeout, third succeeds
        mock_success_response = MagicMock()
        mock_success_response.json.return_value = {"success": True}

        mock_client_instance.get.side_effect = [
            httpx.TimeoutException("Timeout"),
            httpx.TimeoutException("Timeout"),
            mock_success_response,
        ]
        mock_httpx_client.return_value = mock_client_instance

        client = EurostatClient(max_retries=3, retry_backoff=1.0)
        result = client.get_dataset("demo_pjan")

        assert result == {"success": True}
        assert mock_client_instance.get.call_count == 3
        # Should have slept twice (after first two failures)
        assert mock_sleep.call_count == 2

    @patch("time.sleep")
    @patch("backend.src.data_acquisition.eurostat.client.httpx.Client")
    def test_retry_backoff_timing(
        self, mock_httpx_client: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """Test exponential backoff timing."""
        mock_client_instance = MagicMock()
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)

        mock_success_response = MagicMock()
        mock_success_response.json.return_value = {}

        mock_client_instance.get.side_effect = [
            httpx.TimeoutException("Timeout"),
            httpx.TimeoutException("Timeout"),
            mock_success_response,
        ]
        mock_httpx_client.return_value = mock_client_instance

        client = EurostatClient(max_retries=3, retry_backoff=1.0)
        client.get_dataset("demo_pjan")

        # Check backoff timing: 1.0 * 2^0 = 1.0, 1.0 * 2^1 = 2.0
        sleep_calls = [call.args[0] for call in mock_sleep.call_args_list]
        assert sleep_calls == [1.0, 2.0]

    @patch("time.sleep")
    @patch("backend.src.data_acquisition.eurostat.client.httpx.Client")
    def test_retry_on_5xx_error(
        self, mock_httpx_client: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """Test retry behavior on 5xx server errors."""
        mock_client_instance = MagicMock()
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)

        # Create 500 error response
        error_response = MagicMock()
        error_response.status_code = 500
        error_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server Error", request=MagicMock(), response=error_response
        )

        success_response = MagicMock()
        success_response.json.return_value = {"success": True}
        success_response.raise_for_status.return_value = None

        mock_client_instance.get.side_effect = [error_response, success_response]
        mock_httpx_client.return_value = mock_client_instance

        client = EurostatClient(max_retries=2)
        result = client.get_dataset("demo_pjan")

        assert result == {"success": True}
        assert mock_client_instance.get.call_count == 2

    @patch("time.sleep")
    @patch("backend.src.data_acquisition.eurostat.client.httpx.Client")
    def test_retry_on_429_too_many_requests(
        self, mock_httpx_client: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """Test retry behavior on 429 Too Many Requests."""
        mock_client_instance = MagicMock()
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)

        # Create 429 error response
        error_response = MagicMock()
        error_response.status_code = 429
        error_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Too Many Requests", request=MagicMock(), response=error_response
        )

        success_response = MagicMock()
        success_response.json.return_value = {"success": True}
        success_response.raise_for_status.return_value = None

        mock_client_instance.get.side_effect = [error_response, success_response]
        mock_httpx_client.return_value = mock_client_instance

        client = EurostatClient(max_retries=2)
        result = client.get_dataset("demo_pjan")

        assert result == {"success": True}
        assert mock_client_instance.get.call_count == 2

    @patch("backend.src.data_acquisition.eurostat.client.httpx.Client")
    def test_no_retry_on_4xx_error(self, mock_httpx_client: MagicMock) -> None:
        """Test that 4xx errors (except 429) are not retried."""
        mock_client_instance = MagicMock()
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)

        # Create 400 error response
        error_response = MagicMock()
        error_response.status_code = 400
        error_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=MagicMock(), response=error_response
        )

        mock_client_instance.get.return_value = error_response
        mock_httpx_client.return_value = mock_client_instance

        client = EurostatClient(max_retries=3)

        with pytest.raises(httpx.HTTPStatusError):
            client.get_dataset("demo_pjan")

        # Should only be called once (no retries)
        assert mock_client_instance.get.call_count == 1

    @patch("backend.src.data_acquisition.eurostat.client.httpx.Client")
    def test_no_retry_on_404_error(self, mock_httpx_client: MagicMock) -> None:
        """Test that 404 errors are not retried."""
        mock_client_instance = MagicMock()
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)

        # Create 404 error response
        error_response = MagicMock()
        error_response.status_code = 404
        error_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=error_response
        )

        mock_client_instance.get.return_value = error_response
        mock_httpx_client.return_value = mock_client_instance

        client = EurostatClient(max_retries=3)

        with pytest.raises(httpx.HTTPStatusError):
            client.get_dataset("demo_pjan")

        assert mock_client_instance.get.call_count == 1

    @patch("time.sleep")
    @patch("backend.src.data_acquisition.eurostat.client.httpx.Client")
    def test_max_retries_exceeded(
        self, mock_httpx_client: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """Test that exception is raised when max retries exceeded."""
        mock_client_instance = MagicMock()
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)

        # Always timeout
        mock_client_instance.get.side_effect = httpx.TimeoutException("Timeout")
        mock_httpx_client.return_value = mock_client_instance

        client = EurostatClient(max_retries=2)

        with pytest.raises(httpx.TimeoutException):
            client.get_dataset("demo_pjan")

        # Initial attempt + 2 retries = 3 calls
        assert mock_client_instance.get.call_count == 3

    @patch("time.sleep")
    @patch("backend.src.data_acquisition.eurostat.client.httpx.Client")
    def test_request_error_retry(
        self, mock_httpx_client: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """Test retry on general request errors."""
        mock_client_instance = MagicMock()
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)

        success_response = MagicMock()
        success_response.json.return_value = {"success": True}

        mock_client_instance.get.side_effect = [
            httpx.RequestError("Connection failed"),
            success_response,
        ]
        mock_httpx_client.return_value = mock_client_instance

        client = EurostatClient(max_retries=2)
        result = client.get_dataset("demo_pjan")

        assert result == {"success": True}
