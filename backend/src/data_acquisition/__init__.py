"""
Data Acquisition Module

This module provides functionality for acquiring demographic data from various sources:
- CSV files
- JSON files
- HTTP APIs
"""

from .base import AcquisitionResult, DataAcquirer
from .eurostat.acquirer import EurostatAcquirer
from .factory import DataAcquirerFactory
from .pipeline import DataAcquisitionPipeline

__all__ = [
    "AcquisitionResult",
    "DataAcquirer",
    "DataAcquirerFactory",
    "DataAcquisitionPipeline",
    "EurostatAcquirer",
]
