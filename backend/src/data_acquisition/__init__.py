"""
Data Acquisition Module

This module provides functionality for acquiring demographic data from various sources:
- CSV files
- JSON files
- HTTP APIs
"""

from .base import AcquisitionResult, DataAcquirer
from .factory import DataAcquirerFactory
from .pipeline import DataAcquisitionPipeline
from .eurostat.acquirer import EurostatAcquirer

__all__ = [
    "DataAcquirer",
    "AcquisitionResult",
    "DataAcquirerFactory",
    "DataAcquisitionPipeline",
    "EurostatAcquirer",
]

