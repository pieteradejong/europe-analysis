"""
Base Data Acquisition Interface

This module defines the abstract base class for all data acquirers.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AcquisitionResult:
    """Result of a data acquisition operation."""

    success: bool
    data: list[dict[str, Any]] | None = None
    metadata: dict[str, Any] | None = None
    error: str | None = None
    records_count: int = 0

    def __post_init__(self) -> None:
        """Calculate records count if data is provided."""
        if self.data is not None:
            self.records_count = len(self.data)


class DataAcquirer(ABC):
    """
    Abstract base class for data acquisition from various sources.

    All data acquirers must implement the acquire method which returns
    raw data in a list of dictionaries format.
    """

    def __init__(self, source: str, **kwargs: Any) -> None:
        """
        Initialize the data acquirer.

        Args:
            source: Source identifier (file path, URL, etc.)
            **kwargs: Additional source-specific parameters
        """
        self.source = source
        self.config = kwargs
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def acquire(self) -> AcquisitionResult:
        """
        Acquire data from the source.

        Returns:
            AcquisitionResult containing the acquired data or error information
        """
        pass

    @abstractmethod
    def validate_source(self) -> bool:
        """
        Validate that the source is accessible and valid.

        Returns:
            True if source is valid, False otherwise
        """
        pass

    def get_metadata(self) -> dict[str, Any]:
        """
        Get metadata about the source.

        Returns:
            Dictionary containing source metadata
        """
        return {
            "source": self.source,
            "type": self.__class__.__name__,
            "config": self.config,
        }
