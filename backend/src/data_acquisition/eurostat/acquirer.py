"""
Eurostat Data Acquirer.

Source is a Eurostat dataset id (e.g. 'demo_pjan'). Filters are passed through
as query params to the Eurostat Statistics API.
"""

from __future__ import annotations

import logging
from typing import Any

from ..base import AcquisitionResult, DataAcquirer
from .client import EurostatClient
from .datasets import DATASETS, EurostatDatasetConfig
from .jsonstat import (
    flatten_jsonstat_dataset,
    normalize_age,
    normalize_sex,
    normalize_time_to_year,
)

logger = logging.getLogger(__name__)


class EurostatAcquirer(DataAcquirer):
    """
    Acquire data from Eurostat Statistics API (JSON-stat 2.0).

    - `source` is the dataset id (e.g. 'demo_pjan')
    - `params` controls slicing (geo, time, sex, age, etc.)
    """

    def __init__(
        self,
        source: str,
        params: dict[str, Any] | None = None,
        base_url: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_backoff: float = 1.0,
        dataset_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(source, **kwargs)
        self.dataset_id = dataset_id or source
        self.params = params or {}

        self.config_obj: EurostatDatasetConfig = DATASETS.get(
            self.dataset_id,
            EurostatDatasetConfig(dataset_id=self.dataset_id),
        )

        self.client = EurostatClient(
            base_url=base_url
            or "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/",
            timeout=timeout,
            max_retries=max_retries,
            retry_backoff=retry_backoff,
        )

    def validate_source(self) -> bool:
        # Dataset ids are typically short strings; we just ensure non-empty.
        if not self.dataset_id or not isinstance(self.dataset_id, str):
            self.logger.error("Invalid Eurostat dataset id: %r", self.dataset_id)
            return False
        return True

    def acquire(self) -> AcquisitionResult:
        if not self.validate_source():
            return AcquisitionResult(
                success=False, error=f"Invalid dataset id: {self.dataset_id}"
            )

        # Merge defaults + caller params
        merged_params: dict[str, Any] = {}
        if self.config_obj.default_params:
            merged_params.update(self.config_obj.default_params)
        merged_params.update(self.params)

        try:
            raw = self.client.get_dataset(self.dataset_id, params=merged_params)
            # The Statistics API returns a JSON-stat dataset at the root.
            flat = flatten_jsonstat_dataset(raw)

            # Map to a shape friendly for DemographicNormalizer (keys it understands).
            # We keep both region_code and region_name (if label available).
            out: list[dict[str, Any]] = []
            for rec in flat:
                geo = rec.get(self.config_obj.dim_geo)
                geo_label = rec.get(f"{self.config_obj.dim_geo}__label")
                time_code = rec.get(self.config_obj.dim_time)
                time_label = rec.get(f"{self.config_obj.dim_time}__label")
                sex_code = rec.get(self.config_obj.dim_sex)
                sex_label = rec.get(f"{self.config_obj.dim_sex}__label")
                age_code = rec.get(self.config_obj.dim_age)
                age_label = rec.get(f"{self.config_obj.dim_age}__label")

                year = normalize_time_to_year(
                    str(time_code) if time_code is not None else None,
                    str(time_label) if time_label is not None else None,
                )
                gender = normalize_sex(
                    str(sex_code) if sex_code is not None else None,
                    str(sex_label) if sex_label is not None else None,
                )
                age_group = normalize_age(
                    str(age_code) if age_code is not None else None,
                    str(age_label) if age_label is not None else None,
                )

                value = rec.get(self.config_obj.value_field)
                if value is None:
                    continue

                out.append(
                    {
                        "region_code": str(geo) if geo is not None else None,
                        "region_name": (
                            str(geo_label) if geo_label is not None else str(geo)
                        ),
                        "year": year,
                        "gender": gender,
                        "age_group": age_group,
                        "population": value,
                        "_eurostat": {
                            "dataset_id": self.dataset_id,
                            "params": merged_params,
                        },
                    }
                )

            return AcquisitionResult(
                success=True,
                data=out,
                metadata={
                    "dataset_id": self.dataset_id,
                    "params": merged_params,
                    "records_flattened": len(flat),
                    "records_mapped": len(out),
                },
                records_count=len(out),
            )
        except Exception as exc:
            self.logger.error("Eurostat acquisition failed: %s", exc, exc_info=True)
            return AcquisitionResult(success=False, error=str(exc))
