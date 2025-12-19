"""Tests for configuration management."""

import json
import os
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from backend.src.library import AppConfig, load_json_config

# Constants
DEFAULT_API_PORT = 8000


@pytest.fixture
def clean_env() -> Generator[None, None, None]:
    """Clean environment fixture that restores original env after test."""
    original_env = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(original_env)


def test_app_config_defaults() -> None:
    """Test AppConfig default values when no env vars override."""
    # Create config with explicit defaults (not from env)
    config = AppConfig()
    # These are the defaults unless env vars override them
    assert config.ENV in {"development", "testing", "production"}
    assert isinstance(config.DEBUG, bool)
    assert config.APP_NAME is not None
    assert config.API_HOST is not None
    assert config.API_PORT == DEFAULT_API_PORT
    assert config.LOG_LEVEL in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


def test_app_config_env_override(clean_env: None) -> None:
    """Test environment variable overrides."""
    os.environ.update(
        {
            "APP_ENV": "testing",
            "APP_DEBUG": "true",
            "APP_NAME": "Test App",
            "API_HOST": "127.0.0.1",
            "API_PORT": "8000",
            "LOG_LEVEL": "DEBUG",
        }
    )
    config = AppConfig()
    assert config.ENV == "testing"
    assert config.DEBUG is True
    assert config.APP_NAME == "Test App"
    assert config.API_HOST == "127.0.0.1"
    assert config.API_PORT == DEFAULT_API_PORT
    assert config.LOG_LEVEL == "DEBUG"


def test_app_config_validation() -> None:
    """Test configuration validation."""
    from pydantic import ValidationError

    # Test invalid ENV
    with pytest.raises(ValidationError, match="ENV must be one of"):
        AppConfig(ENV="invalid")

    # Test invalid LOG_LEVEL
    with pytest.raises(ValidationError, match="LOG_LEVEL must be one of"):
        AppConfig(LOG_LEVEL="INVALID")


def test_json_config_loading(temp_json_config: Path) -> None:
    """Test JSON configuration loading."""
    config = load_json_config(str(temp_json_config))
    assert config["CANDIDATE_ID"] == "test-123"


def test_json_config_missing_required() -> None:
    """Test JSON config with missing required fields."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write('{"other_field": "value"}')
        f.flush()
        try:
            with pytest.raises(ValueError, match="Missing required fields"):
                load_json_config(f.name)
        finally:
            os.unlink(f.name)


def test_json_config_invalid_json() -> None:
    """Test loading invalid JSON config."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write('{"invalid": json}')
        f.flush()
        try:
            with pytest.raises(json.JSONDecodeError):
                load_json_config(f.name)
        finally:
            os.unlink(f.name)
