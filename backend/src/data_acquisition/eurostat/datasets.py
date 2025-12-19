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

# Live births by mother's age
DEMO_FASEC = EurostatDatasetConfig(
    dataset_id="demo_fasec",
    dim_age="age",  # Mother's age
    default_params={},
)

# Deaths by age and sex
DEMO_MAGEC = EurostatDatasetConfig(
    dataset_id="demo_magec",
    default_params={},
)

# Immigration by citizenship
MIGR_IMM1CTZ = EurostatDatasetConfig(
    dataset_id="migr_imm1ctz",
    dim_age="age",
    default_params={},
)

# Emigration by citizenship
MIGR_EMI1CTZ = EurostatDatasetConfig(
    dataset_id="migr_emi1ctz",
    dim_age="age",
    default_params={},
)

# Industrial Production Index (monthly)
STS_INPR_M = EurostatDatasetConfig(
    dataset_id="sts_inpr_m",
    dim_geo="geo",
    dim_time="time",
    dim_sex="",  # Not applicable for industrial data
    dim_age="",  # Not applicable for industrial data
    default_params={
        "unit": "I15",  # Index 2015=100
        "s_adj": "SCA",  # Seasonally and calendar adjusted
        "nace_r2": "B-D",  # Mining, manufacturing, electricity
    },
)


DATASETS: dict[str, EurostatDatasetConfig] = {
    DEMO_PJAN.dataset_id: DEMO_PJAN,
    DEMO_FASEC.dataset_id: DEMO_FASEC,
    DEMO_MAGEC.dataset_id: DEMO_MAGEC,
    MIGR_IMM1CTZ.dataset_id: MIGR_IMM1CTZ,
    MIGR_EMI1CTZ.dataset_id: MIGR_EMI1CTZ,
    STS_INPR_M.dataset_id: STS_INPR_M,
}
