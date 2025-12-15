"""
JSON Data Acquirer

This module provides functionality for acquiring demographic data from JSON files.
Supports various JSON formats including arrays and nested objects.
"""

import json
import logging
from pathlib import Path
from typing import Any

from .base import AcquisitionResult, DataAcquirer

logger = logging.getLogger(__name__)


class JSONAcquirer(DataAcquirer):
    """
    Acquires data from JSON files.

    Supports:
    - Arrays of objects: [{"key": "value"}, ...]
    - Single objects: {"key": "value"}
    - Nested structures with data_path specification
    """

    def __init__(
        self,
        source: str,
        encoding: str = "utf-8",
        data_path: str | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize JSON acquirer.

        Args:
            source: Path to JSON file
            encoding: File encoding (default: utf-8)
            data_path: JSONPath-like path to data array (e.g., "data.items")
                      If None, assumes root is array or extracts from common keys
            **kwargs: Additional parameters
        """
        super().__init__(source, **kwargs)
        self.encoding = encoding
        self.data_path = data_path
        self.file_path = Path(source)

    def validate_source(self) -> bool:
        """
        Validate that the JSON file exists and is readable.

        Returns:
            True if file is valid, False otherwise
        """
        if not self.file_path.exists():
            self.logger.error("JSON file does not exist: %s", self.source)
            return False

        if not self.file_path.is_file():
            self.logger.error("Source is not a file: %s", self.source)
            return False

        if not self.file_path.suffix.lower() == ".json":
            self.logger.warning("File does not have .json extension: %s", self.source)

        return True

    def _extract_data_path(self, data: dict[str, Any] | list[Any]) -> list[dict[str, Any]]:
        """
        Extract data array from JSON structure using data_path or auto-detection.

        Args:
            data: Parsed JSON data

        Returns:
            List of dictionaries representing records
        """
        if isinstance(data, list):
            # Already an array
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
                        "Data path '%s' not found in JSON, trying auto-detection",
                        self.data_path,
                    )
                    break
            else:
                if isinstance(current, list):
                    return [item for item in current if isinstance(item, dict)]
                if isinstance(current, dict):
                    return [current]

        # Auto-detect common patterns
        # Try common keys that might contain arrays
        for key in ["data", "items", "results", "records", "values"]:
            if key in data and isinstance(data[key], list):
                return [item for item in data[key] if isinstance(item, dict)]

        # If it's a single object, wrap it in a list
        if isinstance(data, dict):
            return [data]

        return []

    def acquire(self) -> AcquisitionResult:
        """
        Acquire data from JSON file.

        Returns:
            AcquisitionResult containing the JSON data as list of dictionaries
        """
        if not self.validate_source():
            return AcquisitionResult(
                success=False,
                error=f"Invalid JSON source: {self.source}",
            )

        try:
            metadata: dict[str, Any] = {
                "file_path": str(self.file_path),
                "file_size": self.file_path.stat().st_size,
                "encoding": self.encoding,
                "data_path": self.data_path,
            }

            with open(self.file_path, encoding=self.encoding) as jsonfile:
                raw_data = json.load(jsonfile)

            metadata["raw_structure"] = (
                "array" if isinstance(raw_data, list) else "object"
            )

            # Extract data array
            data = self._extract_data_path(raw_data)

            if not data:
                return AcquisitionResult(
                    success=False,
                    error=f"No data found in JSON file: {self.source}. "
                    "Expected array or object with data array.",
                )

            metadata["records_extracted"] = len(data)
            if data:
                metadata["sample_keys"] = list(data[0].keys())

            self.logger.info(
                "Successfully acquired %d records from JSON: %s", len(data), self.source
            )

            return AcquisitionResult(
                success=True,
                data=data,
                metadata=metadata,
                records_count=len(data),
            )

        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in file: {self.source} - {e}"
            self.logger.error(error_msg)
            return AcquisitionResult(success=False, error=error_msg)

        except PermissionError as e:
            error_msg = f"Permission denied reading JSON file: {self.source}"
            self.logger.error(error_msg)
            return AcquisitionResult(success=False, error=error_msg)

        except UnicodeDecodeError as e:
            error_msg = f"Encoding error reading JSON file: {self.source} - {e}"
            self.logger.error(error_msg)
            return AcquisitionResult(success=False, error=error_msg)

        except Exception as e:
            error_msg = f"Unexpected error reading JSON file: {self.source} - {e}"
            self.logger.error(error_msg, exc_info=True)
            return AcquisitionResult(success=False, error=error_msg)

