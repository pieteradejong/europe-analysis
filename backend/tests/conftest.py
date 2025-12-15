"""Shared test fixtures."""

import os
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from backend.src.library import AppConfig


@pytest.fixture
def temp_env_file() -> Generator[Path, None, None]:
    """Create a temporary .env file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write(
            """
APP_ENV=testing
APP_DEBUG=true
APP_NAME=Test App
APP_VERSION=0.1.0
API_HOST=127.0.0.1
API_PORT=8000
LOG_LEVEL=DEBUG
        """.strip()
        )
    yield Path(f.name)
    os.unlink(f.name)


@pytest.fixture
def temp_json_config() -> Generator[Path, None, None]:
    """Create a temporary JSON config file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write('{"CANDIDATE_ID": "test-123"}')
    yield Path(f.name)
    os.unlink(f.name)


@pytest.fixture
def app_config(temp_env_file: Path) -> AppConfig:
    """Create an AppConfig instance for testing."""
    return AppConfig(_env_file=str(temp_env_file))
