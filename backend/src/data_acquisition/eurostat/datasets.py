"""
Eurostat dataset configurations.

These configs describe how to map Eurostat JSON-stat dimensions into our
standardized fields used by DemographicNormalizer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EurostatDatasetConfig:
    dataset_id: str
    # Dimension ids in JSON-stat
    dim_geo: str = "geo"
    dim_time: str = "time"
    dim_sex: str = "sex"
    dim_age: str = "age"
    # Value field name in flattened JSON-stat
    value_field: str = "value"
    # Defaults to apply if caller doesn't provide.
    default_params: dict[str, Any] | None = None


# Population on 1 January by age and sex (commonly used for pyramids).
# Dataset id can vary; the canonical Eurostat id is typically 'demo_pjan'.
DEMO_PJAN = EurostatDatasetConfig(
    dataset_id="demo_pjan",
    default_params={
        # Keep defaults minimal; caller can override.
        # Example common filters:
        # "unit": "NR",  # number of persons
    },
)


DATASETS: dict[str, EurostatDatasetConfig] = {
    DEMO_PJAN.dataset_id: DEMO_PJAN,
}


