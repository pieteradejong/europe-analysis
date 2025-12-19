"""
Industrial Data Normalizer

This module provides functionality for normalizing industrial production data from
Eurostat and other sources into a standardized structure suitable for database storage.
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Constants
MAX_MONTH = 12


class IndustrialNormalizer:
    """
    Normalizes industrial data from various formats into standardized structure.

    Handles:
    - Time period parsing (YYYY-MM format for monthly data)
    - NACE industry code extraction
    - Region code and name extraction
    - Index value normalization
    - Unit identification
    """

    def __init__(self) -> None:
        """Initialize the normalizer."""
        self.logger = logging.getLogger(__name__)

    def parse_time_period(self, time_str: str | None) -> tuple[int | None, int | None]:
        """
        Parse time period string into year and month.

        Args:
            time_str: Time period string (e.g., "2023M01", "2023-01", "2023")

        Returns:
            Tuple of (year, month) where month can be None for annual data
        """
        if time_str is None:
            return (None, None)

        time_str = str(time_str).strip()

        # Try YYYY-MM or YYYYMM format
        match = re.search(r"(\d{4})[-M]?(\d{2})", time_str)
        if match:
            year = int(match.group(1))
            month = int(match.group(2))
            if 1 <= month <= MAX_MONTH:
                return (year, month)

        # Try just year
        match = re.search(r"^(\d{4})$", time_str)
        if match:
            return (int(match.group(1)), None)

        self.logger.warning("Could not parse time period: %s", time_str)
        return (None, None)

    def normalize_nace_code(self, nace_str: str | None) -> str | None:
        """
        Normalize NACE industry code.

        Args:
            nace_str: NACE code string (e.g., "B-D", "C", "C10-C12")

        Returns:
            Normalized NACE code or None
        """
        if nace_str is None:
            return None

        # Clean and uppercase the code
        nace_str = str(nace_str).strip().upper()

        # Remove any prefixes like "NACE_"
        nace_str = re.sub(r"^NACE_?", "", nace_str)

        return nace_str if nace_str else None

    def _extract_first_match(
        self, record: dict[str, Any], keys: list[str]
    ) -> str | None:
        """Extract first matching value from record for given keys."""
        for key in keys:
            if record.get(key):
                return str(record[key]).strip()
        return None

    def _extract_index_value(self, record: dict[str, Any]) -> int | None:
        """Extract and parse index value from record."""
        for key in ["value", "index_value", "index", "production_index"]:
            if key in record and record[key] is not None:
                try:
                    val = float(str(record[key]))
                    return round(val)
                except (ValueError, TypeError):
                    continue
        return None

    def normalize_record(  # noqa: PLR0912
        self,
        record: dict[str, Any],
        field_mapping: dict[str, str] | None = None,
    ) -> dict[str, Any] | None:
        """
        Normalize a single industrial data record.

        Args:
            record: Raw record dictionary
            field_mapping: Optional mapping from source fields to standard fields

        Returns:
            Normalized record dictionary or None if record is invalid
        """
        if field_mapping:
            # Apply field mapping
            mapped_record: dict[str, Any] = {}
            for source_key, target_key in field_mapping.items():
                if source_key in record:
                    mapped_record[target_key] = record[source_key]
            record = mapped_record

        normalized: dict[str, Any] = {}

        # Extract and normalize region
        region_code = None
        region_name = None
        for key in ["region_code", "geo", "region", "code", "iso_code"]:
            if record.get(key):
                region_code = str(record[key]).strip()
                break
        for key in ["region_name", "name", "country", "area"]:
            if record.get(key):
                region_name = str(record[key]).strip()
                break

        if not region_code and not region_name:
            self.logger.warning("No region information found in record: %s", record)
            return None

        normalized["region_code"] = region_code or region_name
        normalized["region_name"] = region_name or region_code

        # Extract and normalize time period
        year = None
        month = None
        for key in ["time", "period", "date", "year"]:
            if record.get(key):
                year, month = self.parse_time_period(record[key])
                if year is not None:
                    break

        normalized["year"] = year
        normalized["month"] = month

        # Extract NACE code
        nace_code = None
        for key in ["nace_r2", "nace", "nace_code", "industry", "sector"]:
            if record.get(key):
                nace_code = self.normalize_nace_code(record[key])
                break

        normalized["nace_code"] = nace_code

        # Extract index value
        index_value = None
        for key in ["value", "index_value", "index", "production_index"]:
            if key in record and record[key] is not None:
                try:
                    # Handle potential float values
                    val = float(str(record[key]))
                    index_value = round(val)
                    break
                except (ValueError, TypeError):
                    continue

        if index_value is None:
            self.logger.warning("No index value found in record: %s", record)
            return None

        normalized["index_value"] = index_value

        # Extract unit
        unit = None
        for key in ["unit", "unit_measure", "measure"]:
            if record.get(key):
                unit = str(record[key]).strip()
                break

        normalized["unit"] = unit

        # Store original record for reference
        normalized["_original"] = record

        return normalized

    def normalize_batch(
        self,
        records: list[dict[str, Any]],
        field_mapping: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Normalize a batch of industrial data records.

        Args:
            records: List of raw record dictionaries
            field_mapping: Optional mapping from source fields to standard fields

        Returns:
            List of normalized record dictionaries
        """
        normalized_records: list[dict[str, Any]] = []

        for record in records:
            normalized = self.normalize_record(record, field_mapping)
            if normalized is not None:
                # Remove helper fields
                normalized.pop("_original", None)
                normalized_records.append(normalized)

        self.logger.info(
            "Normalized %d industrial records into %d normalized records",
            len(records),
            len(normalized_records),
        )

        return normalized_records
