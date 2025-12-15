import csv
import json
import logging
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict

"""
Library of re-usable functionality.
"""


class AppConfig(BaseSettings):
    """Application configuration with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )

    # Environment
    ENV: str = Field(default="development", env="APP_ENV")
    DEBUG: bool = Field(default=False, env="APP_DEBUG")

    # Application
    APP_NAME: str = Field(default="Python Base App", env="APP_NAME")
    APP_VERSION: str = Field(default="0.1.0", env="APP_VERSION")

    # API
    API_HOST: str = Field(default="0.0.0.0", env="API_HOST")
    API_PORT: int = Field(default=8000, env="API_PORT")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", env="LOG_FORMAT"
    )
    LOG_FILE: Path | None = Field(default=None, env="LOG_FILE")

    @validator("ENV")
    def validate_env(cls, v: str) -> str:
        """Validate environment setting."""
        allowed = {"development", "testing", "production"}
        if v not in allowed:
            raise ValueError(f"ENV must be one of {allowed}")
        return v

    @validator("LOG_LEVEL")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level setting."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return v


class TextColor(Enum):
    """ANSI color codes for terminal output."""

    RED = "\033[91m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    PURPLE = "\033[95m"
    MAGENTA = "\033[35m"
    CYAN = "\033[96m"
    BLUE = "\033[94m"
    REGULAR = "\033[0m"


def setup_logging(config: AppConfig) -> None:
    """
    Configure logging based on application settings.

    Args:
        config: Application configuration object
    """
    log_handlers = []

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(config.LOG_FORMAT))
    log_handlers.append(console_handler)

    # File handler if LOG_FILE is set
    if config.LOG_FILE:
        config.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(config.LOG_FILE)
        file_handler.setFormatter(logging.Formatter(config.LOG_FORMAT))
        log_handlers.append(file_handler)

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL), handlers=log_handlers, force=True
    )


def print_colored(text: str, color: TextColor) -> None:
    """
    Print colored text to the terminal.

    Args:
        text: Text to print
        color: Color to use
    """
    print(f"{color.value}{text}{TextColor.REGULAR.value}")


# Example usage
print_colored("Hello, World!", TextColor.RED)
print_colored("This is green text!", TextColor.GREEN)


def read_csv_file(file_path: str) -> list[dict[str, Any]]:
    """
    Read a CSV file and return a list of dictionaries.

    Args:
        file_path: Path to the CSV file

    Returns:
        List of dictionaries where each dict represents a row

    Raises:
        FileNotFoundError: If the file doesn't exist
        csv.Error: If the CSV file is malformed
    """
    data = []
    with open(file_path, encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            data.append(dict(row))
    return data


def load_json_config(file_path: str) -> dict[str, Any]:
    """
    Load and validate JSON configuration file.

    Args:
        file_path: Path to the JSON config file

    Returns:
        Dictionary containing the configuration

    Raises:
        FileNotFoundError: If the config file doesn't exist
        json.JSONDecodeError: If the JSON is invalid
        ValueError: If required fields are missing
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            config_data = json.load(f)

        # Validate required fields
        required_fields = {"CANDIDATE_ID"}
        missing_fields = required_fields - set(config_data.keys())
        if missing_fields:
            raise ValueError(f"Missing required fields in config: {missing_fields}")

        return config_data

    except FileNotFoundError:
        logging.error("Configuration file %s does not exist", file_path)
        raise
    except json.JSONDecodeError:
        logging.error("Error decoding %s. Ensure it is valid JSON", file_path)
        raise
    except Exception as e:
        logging.error("Unexpected error loading config: %s", e)
        raise


# Initialize global config
config = AppConfig()
