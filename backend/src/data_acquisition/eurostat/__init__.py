"""
Eurostat data acquisition utilities.

Implements a Eurostat-specific acquirer that uses the Eurostat Statistics API
and parses JSON-stat 2.0 responses into flat records compatible with our
normalization + storage pipeline.
"""

from .acquirer import EurostatAcquirer

__all__ = ["EurostatAcquirer"]


