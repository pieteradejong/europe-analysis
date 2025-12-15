"""Integration tests for application startup and initialization."""

import logging
import os
from collections.abc import Generator
from pathlib import Path

import pytest

from backend.src.main import init_app, main


@pytest.fixture
def test_env_vars() -> Generator[None, None, None]:
    """Set up test environment variables."""
    # Save original environment
    original_env = dict(os.environ)

    # Set test environment
    os.environ.update(
        {
            "APP_ENV": "testing",
            "APP_DEBUG": "true",
            "APP_NAME": "Test App",
            "APP_VERSION": "0.1.0",
            "API_HOST": "127.0.0.1",
            "API_PORT": "8000",
            "LOG_LEVEL": "DEBUG",
        }
    )

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def test_log_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary log directory."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    yield log_dir


def test_app_initialization(test_env_vars: None, test_log_dir: Path) -> None:
    """Test application initialization with test environment."""
    # Set log file path
    os.environ["LOG_FILE"] = str(test_log_dir / "test.log")

    # Initialize app
    init_app()

    # Verify logging is set up
    logger = logging.getLogger(__name__)
    assert logger.level == logging.DEBUG

    # Verify log file exists
    log_file = test_log_dir / "test.log"
    assert log_file.exists()

    # Verify log content
    log_content = log_file.read_text()
    assert "Initializing Test App v0.1.0" in log_content
    assert "Environment: testing (Debug: True)" in log_content


def test_app_initialization_with_json_config(
    test_env_vars: None, test_log_dir: Path, temp_json_config: Path
) -> None:
    """Test application initialization with JSON config."""
    # Set log file path
    os.environ["LOG_FILE"] = str(test_log_dir / "test.log")

    # Initialize app with JSON config
    init_app(config_path=temp_json_config)

    # Verify log content includes JSON config info
    log_file = test_log_dir / "test.log"
    log_content = log_file.read_text()
    assert f"Loaded JSON configuration from {temp_json_config}" in log_content


def test_app_initialization_invalid_env() -> None:
    """Test application initialization with invalid environment."""
    # Set invalid environment
    os.environ["APP_ENV"] = "invalid"

    # Verify initialization fails
    with pytest.raises(ValueError, match="ENV must be one of"):
        init_app()


def test_app_initialization_missing_required_var() -> None:
    """Test application initialization with missing required variable."""
    # Remove required variable
    if "APP_NAME" in os.environ:
        del os.environ["APP_NAME"]

    # Verify initialization fails with specific exception
    with pytest.raises((ValueError, KeyError)):
        init_app()


@pytest.mark.asyncio
async def test_app_startup(test_env_vars: None, test_log_dir: Path) -> None:
    """Test application startup process."""
    # Set log file path
    os.environ["LOG_FILE"] = str(test_log_dir / "test.log")

    # Initialize and start app
    init_app()
    main()

    # Verify startup logs
    log_file = test_log_dir / "test.log"
    log_content = log_file.read_text()
    assert "Starting application..." in log_content
    assert "Application shutdown complete" in log_content
