"""
Data Normalizer

This module provides functionality for normalizing demographic data from various
input formats into a standardized structure suitable for database storage.
"""

import logging
import re
from typing import Any, ClassVar

logger = logging.getLogger(__name__)

# Minimum length for finding multiple age numbers
MIN_AGE_NUMBERS = 2


class DemographicNormalizer:
    """
    Normalizes demographic data from various formats into standardized structure.

    Handles:
    - Different age group formats (0-4, 5-9 vs 0-5, 5-10, etc.)
    - Gender category normalization (M/F, Male/Female, etc.)
    - Region code and name extraction
    - Year extraction
    - Population count normalization
    """

    # Gender normalization mappings
    GENDER_MAPPINGS: ClassVar[dict[str, str]] = {
        "m": "M",
        "male": "M",
        "masculine": "M",
        "f": "F",
        "female": "F",
        "feminine": "F",
        "t": "Total",
        "o": "O",
        "other": "O",
        "unknown": "O",
        "unspecified": "O",
        "total": "Total",
        "all": "Total",
        "both": "Total",
    }

    # Common age group patterns
    AGE_PATTERNS: ClassVar[list[tuple[str, str]]] = [
        (r"(\d+)\s*-\s*(\d+)", "range"),  # "0-4", "5-9"
        (r"(\d+)\s*to\s*(\d+)", "range"),  # "0 to 4"
        (r"(\d+)\+", "open"),  # "65+", "80+"
        (r"under\s*(\d+)", "under"),  # "under 5"
        (r"over\s*(\d+)", "over"),  # "over 65"
        (r"^(\d+)$", "single"),  # "0", "5", "10"
    ]

    def __init__(self) -> None:
        """Initialize the normalizer."""
        self.logger = logging.getLogger(__name__)

    def normalize_gender(self, gender: str | None) -> str | None:
        """
        Normalize gender value to standard format (M/F/O/Total).

        Args:
            gender: Raw gender value

        Returns:
            Normalized gender value or None
        """
        if gender is None:
            return None

        gender_str = str(gender).strip().lower()
        return self.GENDER_MAPPINGS.get(gender_str, gender_str.upper())

    def parse_age_group(  # noqa: PLR0911
        self, age_str: str | int | None
    ) -> tuple[int | None, int | None]:
        """
        Parse age group string into min and max age.

        Args:
            age_str: Age group string (e.g., "0-4", "65+", "under 5")

        Returns:
            Tuple of (min_age, max_age) where max_age can be None for open-ended
        """
        if age_str is None:
            return (None, None)

        age_str = str(age_str).strip().lower()

        # Try each pattern
        for pattern, pattern_type in self.AGE_PATTERNS:
            match = re.search(pattern, age_str)
            if match:
                if pattern_type == "range":
                    min_age = int(match.group(1))
                    max_age = int(match.group(2)) + 1  # Exclusive upper bound
                    return (min_age, max_age)
                elif pattern_type == "open":
                    min_age = int(match.group(1))
                    return (min_age, None)
                elif pattern_type == "under":
                    max_age = int(match.group(1))
                    return (0, max_age)
                elif pattern_type == "over":
                    min_age = int(match.group(1))
                    return (min_age, None)
                elif pattern_type == "single":
                    age = int(match.group(1))
                    return (age, age + 1)

        # If no pattern matches, try to extract numbers
        numbers = re.findall(r"\d+", age_str)
        if len(numbers) == 1:
            age = int(numbers[0])
            return (age, age + 1)
        elif len(numbers) >= MIN_AGE_NUMBERS:
            return (int(numbers[0]), int(numbers[1]) + 1)

        self.logger.warning("Could not parse age group: %s", age_str)
        return (None, None)

    def normalize_record(  # noqa: PLR0912, PLR0915
        self,
        record: dict[str, Any],
        field_mapping: dict[str, str] | None = None,
    ) -> dict[str, Any] | None:
        """
        Normalize a single demographic record.

        Args:
            record: Raw record dictionary
            field_mapping: Optional mapping from source fields to standard fields
                          e.g., {"age_group": "age", "pop": "population"}

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
        for key in ["region_code", "region", "code", "iso_code", "nuts_code"]:
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

        # Extract and normalize year
        year = None
        for key in ["year", "date", "period", "time"]:
            if record.get(key):
                try:
                    year_val = record[key]
                    if isinstance(year_val, str):
                        # Try to extract year from string (e.g., "2020-01-01" -> 2020)
                        year_match = re.search(r"(\d{4})", year_val)
                        if year_match:
                            year = int(year_match.group(1))
                        else:
                            year = int(year_val)
                    else:
                        year = int(year_val)
                    break
                except (ValueError, TypeError):
                    continue

        if year is None:
            self.logger.warning("No valid year found in record: %s", record)
            # Don't fail, use None as year might be optional
            normalized["year"] = None
        else:
            normalized["year"] = year

        # Extract and normalize age group
        age_min = None
        age_max = None
        for key in ["age", "age_group", "age_range", "age_class"]:
            if record.get(key):
                age_min, age_max = self.parse_age_group(record[key])
                break

        normalized["age_min"] = age_min
        normalized["age_max"] = age_max

        # Extract and normalize gender
        gender = None
        for key in ["gender", "sex", "male_female"]:
            if record.get(key):
                gender = self.normalize_gender(record[key])
                break

        # If gender not found, check for separate male/female columns
        if gender is None:
            male_pop = None
            female_pop = None
            for key in ["male", "m", "men", "population_male"]:
                if record.get(key):
                    try:
                        male_pop = int(float(record[key]))
                        break
                    except (ValueError, TypeError):
                        continue

            for key in ["female", "f", "women", "population_female"]:
                if record.get(key):
                    try:
                        female_pop = int(float(record[key]))
                        break
                    except (ValueError, TypeError):
                        continue

            if male_pop is not None or female_pop is not None:
                # This record represents both genders, we'll need to split it
                # Return None here and let the caller handle splitting
                normalized["_split_gender"] = True
                normalized["_male_pop"] = male_pop or 0
                normalized["_female_pop"] = female_pop or 0
                normalized["gender"] = "Total"
            else:
                normalized["gender"] = "Total"  # Default to Total if not specified
        else:
            normalized["gender"] = gender

        # Extract and normalize population
        population = None
        for key in [
            "population",
            "pop",
            "count",
            "value",
            "total",
            "persons",
            "people",
        ]:
            if key in record and record[key] is not None:
                try:
                    population = int(float(str(record[key])))
                    break
                except (ValueError, TypeError):
                    continue

        if population is None:
            self.logger.warning("No population value found in record: %s", record)
            return None

        normalized["population"] = population

        # Store original record for reference
        normalized["_original"] = record

        return normalized

    def normalize_batch(
        self,
        records: list[dict[str, Any]],
        field_mapping: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Normalize a batch of demographic records.

        Handles records that need to be split (e.g., separate male/female columns).

        Args:
            records: List of raw record dictionaries
            field_mapping: Optional mapping from source fields to standard fields

        Returns:
            List of normalized record dictionaries
        """
        normalized_records: list[dict[str, Any]] = []

        for record in records:
            normalized = self.normalize_record(record, field_mapping)
            if normalized is None:
                continue

            # Check if record needs to be split by gender
            if normalized.get("_split_gender"):
                # Create separate records for male and female
                male_record = normalized.copy()
                male_record["gender"] = "M"
                male_record["population"] = normalized["_male_pop"]
                del male_record["_split_gender"]
                del male_record["_male_pop"]
                del male_record["_female_pop"]
                normalized_records.append(male_record)

                female_record = normalized.copy()
                female_record["gender"] = "F"
                female_record["population"] = normalized["_female_pop"]
                del female_record["_split_gender"]
                del female_record["_male_pop"]
                del female_record["_female_pop"]
                normalized_records.append(female_record)
            else:
                # Remove helper fields
                normalized.pop("_split_gender", None)
                normalized.pop("_male_pop", None)
                normalized.pop("_female_pop", None)
                normalized_records.append(normalized)

        self.logger.info(
            "Normalized %d records into %d normalized records",
            len(records),
            len(normalized_records),
        )

        return normalized_records
