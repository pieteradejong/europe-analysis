"""Integration tests for application startup and initialization."""

import logging
import os
from collections.abc import Generator
from pathlib import Path

import pytest

from backend.src.library import AppConfig, setup_logging

# Constants
DEFAULT_API_PORT = 8000


@pytest.fixture
def clean_env() -> Generator[None, None, None]:
    """Clean environment fixture that restores original env after test."""
    original_env = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def test_log_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary log directory."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    yield log_dir


def test_app_config_from_env(clean_env: None) -> None:
    """Test that AppConfig reads from environment variables."""
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

    config = AppConfig()
    assert config.ENV == "testing"
    assert config.DEBUG is True
    assert config.APP_NAME == "Test App"
    assert config.APP_VERSION == "0.1.0"
    assert config.API_HOST == "127.0.0.1"
    assert config.API_PORT == DEFAULT_API_PORT
    assert config.LOG_LEVEL == "DEBUG"


def test_logging_setup_console(clean_env: None) -> None:
    """Test logging setup with console only."""
    config = AppConfig(LOG_LEVEL="DEBUG")
    setup_logging(config)

    root_logger = logging.getLogger()
    assert root_logger.level == logging.DEBUG


def test_logging_setup_with_file(clean_env: None, test_log_dir: Path) -> None:
    """Test logging setup with file handler."""
    log_file = test_log_dir / "test.log"
    config = AppConfig(LOG_LEVEL="INFO", LOG_FILE=log_file)
    setup_logging(config)

    # Log a message
    logger = logging.getLogger(__name__)
    logger.info("Test log message")

    # Verify log file exists and contains the message
    assert log_file.exists()
    log_content = log_file.read_text()
    assert "Test log message" in log_content


def test_app_config_validation_env() -> None:
    """Test that AppConfig validates ENV values."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="ENV must be one of"):
        AppConfig(ENV="invalid")


def test_app_config_validation_log_level() -> None:
    """Test that AppConfig validates LOG_LEVEL values."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="LOG_LEVEL must be one of"):
        AppConfig(LOG_LEVEL="INVALID")


def test_app_config_defaults() -> None:
    """Test that AppConfig has sensible defaults."""
    # Create config without any env vars set
    config = AppConfig()
    assert config.ENV in {"development", "testing", "production"}
    assert config.APP_NAME is not None
    assert config.API_PORT > 0
    assert config.LOG_LEVEL in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


def test_json_config_loading(temp_json_config: Path) -> None:
    """Test JSON configuration loading."""
    from backend.src.library import load_json_config

    config = load_json_config(str(temp_json_config))
    assert config["CANDIDATE_ID"] == "test-123"


@pytest.mark.asyncio
async def test_main_function_runs() -> None:
    """Test that main function can be called without error."""
    from backend.src.main import main

    # main() should run and complete without error
    main()
