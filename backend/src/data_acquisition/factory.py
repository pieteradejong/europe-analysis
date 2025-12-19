"""
Data Acquirer Factory

This module provides a factory for creating the appropriate data acquirer
based on source type.
"""

import logging
from pathlib import Path
from typing import Any

from .api_acquirer import APIAcquirer
from .base import DataAcquirer
from .csv_acquirer import CSVAcquirer
from .eurostat.acquirer import EurostatAcquirer
from .json_acquirer import JSONAcquirer

logger = logging.getLogger(__name__)


class DataAcquirerFactory:
    """Factory for creating data acquirers based on source type."""

    @staticmethod
    def create(
        source: str,
        source_type: str | None = None,
        **kwargs: Any,
    ) -> DataAcquirer:
        """
        Create appropriate data acquirer based on source type.

        Args:
            source: Source identifier (file path or URL)
            source_type: Explicit source type (csv/json/api). If None, auto-detect
            **kwargs: Additional parameters to pass to acquirer

        Returns:
            DataAcquirer instance

        Raises:
            ValueError: If source type cannot be determined
        """
        # Auto-detect source type if not provided
        if source_type is None:
            source_type = DataAcquirerFactory._detect_source_type(source)

        # Create appropriate acquirer
        if source_type.lower() == "csv":
            return CSVAcquirer(source, **kwargs)
        elif source_type.lower() == "json":
            return JSONAcquirer(source, **kwargs)
        elif source_type.lower() == "api":
            return APIAcquirer(source, **kwargs)
        elif source_type.lower() == "eurostat":
            # For Eurostat, `source` is the dataset id (e.g. 'demo_pjan').
            return EurostatAcquirer(source, **kwargs)
        else:
            raise ValueError(
                f"Unknown source type: {source_type}. "
                "Supported types: csv, json, api, eurostat"
            )

    @staticmethod
    def _detect_source_type(source: str) -> str:
        """
        Auto-detect source type from source identifier.

        Args:
            source: Source identifier (file path or URL)

        Returns:
            Detected source type (csv/json/api)
        """
        # Check if it's a URL
        if source.startswith(("http://", "https://")):
            return "api"

        # Check file extension
        path = Path(source)
        extension = path.suffix.lower()

        if extension == ".csv":
            return "csv"
        elif extension == ".json":
            return "json"
        elif extension:
            # Unknown extension, default to json
            logger.warning("Unknown file extension '%s', defaulting to json", extension)
            return "json"
        else:
            # No extension, try to infer from path
            logger.warning(
                "No file extension found for '%s', defaulting to json", source
            )
            return "json"
