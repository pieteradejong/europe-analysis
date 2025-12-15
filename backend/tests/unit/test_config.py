"""Tests for configuration management."""

import tempfile
from pathlib import Path

import pytest

from backend.src.library import AppConfig, load_json_config

# Constants
DEFAULT_API_PORT = 8000


def test_app_config_defaults() -> None:
    """Test AppConfig default values."""
    config = AppConfig()
    assert config.ENV == "development"
    assert config.DEBUG is False
    assert config.APP_NAME == "Python Base App"
    assert config.API_HOST == "0.0.0.0"
    assert config.API_PORT == DEFAULT_API_PORT
    assert config.LOG_LEVEL == "INFO"


def test_app_config_env_override(temp_env_file: Path) -> None:
    """Test environment variable overrides."""
    config = AppConfig(_env_file=str(temp_env_file))
    assert config.ENV == "testing"
    assert config.DEBUG is True
    assert config.APP_NAME == "Test App"
    assert config.API_HOST == "127.0.0.1"
    assert config.API_PORT == DEFAULT_API_PORT
    assert config.LOG_LEVEL == "DEBUG"


def test_app_config_validation() -> None:
    """Test configuration validation."""
    # Test invalid ENV
    with pytest.raises(ValueError, match="ENV must be one of"):
        AppConfig(ENV="invalid")

    # Test invalid LOG_LEVEL
    with pytest.raises(ValueError, match="LOG_LEVEL must be one of"):
        AppConfig(LOG_LEVEL="INVALID")


def test_json_config_loading(temp_json_config: Path) -> None:
    """Test JSON configuration loading."""
    config = load_json_config(str(temp_json_config))
    assert config["CANDIDATE_ID"] == "test-123"


def test_json_config_missing_required() -> None:
    """Test JSON config with missing required fields."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
        f.write('{"other_field": "value"}')
        f.flush()
        with pytest.raises(ValueError, match="Missing required fields"):
            load_json_config(f.name)


def test_json_config_invalid_json() -> None:
    """Test loading invalid JSON config."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
        f.write('{"invalid": json}')
        f.flush()
        with pytest.raises((ValueError, FileNotFoundError)):
            load_json_config(f.name)
