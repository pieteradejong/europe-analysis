"""Tests for logging configuration."""

import logging
from pathlib import Path

from backend.src.library import AppConfig, setup_logging

# Constants
EXPECTED_HANDLER_COUNT = 2


def test_setup_logging_console_only(app_config: AppConfig) -> None:
    """Test logging setup with console handler only."""
    # Ensure no file logging
    app_config.LOG_FILE = None

    setup_logging(app_config)

    # Check that root logger is configured
    root_logger = logging.getLogger()
    assert root_logger.level == logging.DEBUG
    assert len(root_logger.handlers) >= 1


def test_setup_logging_with_file(app_config: AppConfig, tmp_path: Path) -> None:
    """Test logging setup with file handler."""
    log_file = tmp_path / "test.log"
    app_config.LOG_FILE = log_file

    setup_logging(app_config)

    # Check that root logger is configured
    root_logger = logging.getLogger()
    assert root_logger.level == logging.DEBUG
    assert len(root_logger.handlers) >= EXPECTED_HANDLER_COUNT

    # Check that log file is created
    assert log_file.exists()


def test_setup_logging_creates_directory(app_config: AppConfig, tmp_path: Path) -> None:
    """Test that logging setup creates log directory if it doesn't exist."""
    log_dir = tmp_path / "logs"
    log_file = log_dir / "test.log"
    app_config.LOG_FILE = log_file

    # Ensure directory doesn't exist
    assert not log_dir.exists()

    setup_logging(app_config)

    # Check that directory and file are created
    assert log_dir.exists()
    assert log_file.exists()
