"""Tests for JSON-stat parsing helpers."""

from typing import Any

import pytest

from backend.src.data_acquisition.eurostat.jsonstat import (
    flatten_jsonstat_dataset,
    normalize_age,
    normalize_sex,
    normalize_time_to_year,
)


class TestFlattenJsonstatDataset:
    """Tests for flatten_jsonstat_dataset function."""

    def test_flatten_simple_dataset(self) -> None:
        """Test flattening a simple JSON-stat dataset."""
        dataset: dict[str, Any] = {
            "id": ["geo", "time"],
            "size": [2, 2],
            "dimension": {
                "geo": {
                    "category": {
                        "index": {"DE": 0, "FR": 1},
                        "label": {"DE": "Germany", "FR": "France"},
                    }
                },
                "time": {
                    "category": {
                        "index": {"2022": 0, "2023": 1},
                        "label": {"2022": "2022", "2023": "2023"},
                    }
                },
            },
            "value": [83000000, 83500000, 67000000, 67400000],
        }

        result = flatten_jsonstat_dataset(dataset)

        assert len(result) == 4
        # Check first record (DE, 2022)
        de_2022 = next(r for r in result if r["geo"] == "DE" and r["time"] == "2022")
        assert de_2022["value"] == 83000000
        assert de_2022["geo__label"] == "Germany"

    def test_flatten_with_list_index(
        self, mock_eurostat_sparse_response: dict[str, Any]
    ) -> None:
        """Test flattening dataset with list-style category index."""
        # The sparse response uses list-style index for geo
        result = flatten_jsonstat_dataset(mock_eurostat_sparse_response)

        # 5 non-null values in sparse response
        assert len(result) == 5

    def test_flatten_full_dataset(
        self, mock_eurostat_jsonstat_response: dict[str, Any]
    ) -> None:
        """Test flattening a full JSON-stat response."""
        result = flatten_jsonstat_dataset(mock_eurostat_jsonstat_response)

        # 2 geo * 2 time * 2 sex * 3 age = 24 records
        assert len(result) == 24

        # Check that labels are included
        de_record = next(r for r in result if r["geo"] == "DE")
        assert de_record["geo__label"] == "Germany"

    def test_flatten_sparse_values(
        self, mock_eurostat_sparse_response: dict[str, Any]
    ) -> None:
        """Test flattening dataset with sparse (dict) values."""
        result = flatten_jsonstat_dataset(mock_eurostat_sparse_response)

        # DE, 2022 should be missing (not in sparse dict)
        de_2022 = [r for r in result if r["geo"] == "DE" and r["time"] == "2022"]
        assert len(de_2022) == 0

        # DE, 2021 should be present
        de_2021 = next(r for r in result if r["geo"] == "DE" and r["time"] == "2021")
        assert de_2021["value"] == 83000000

    def test_flatten_skips_null_values(self) -> None:
        """Test that null values are skipped in output."""
        dataset: dict[str, Any] = {
            "id": ["geo"],
            "size": [3],
            "dimension": {
                "geo": {
                    "category": {
                        "index": {"DE": 0, "FR": 1, "IT": 2},
                        "label": {"DE": "Germany", "FR": "France", "IT": "Italy"},
                    }
                },
            },
            "value": [83000000, None, 60000000],
        }

        result = flatten_jsonstat_dataset(dataset)

        assert len(result) == 2
        codes = {r["geo"] for r in result}
        assert codes == {"DE", "IT"}

    def test_flatten_invalid_missing_id(self) -> None:
        """Test error handling for missing id field."""
        dataset: dict[str, Any] = {
            "size": [2],
            "value": [1, 2],
        }

        with pytest.raises(ValueError, match="Invalid JSON-stat dataset"):
            flatten_jsonstat_dataset(dataset)

    def test_flatten_invalid_size_mismatch(self) -> None:
        """Test error handling for id/size length mismatch."""
        dataset: dict[str, Any] = {
            "id": ["geo", "time"],
            "size": [2],  # Should be [2, 2]
            "dimension": {
                "geo": {"category": {"index": {"DE": 0, "FR": 1}}},
                "time": {"category": {"index": {"2022": 0, "2023": 1}}},
            },
            "value": [1, 2, 3, 4],
        }

        with pytest.raises(ValueError, match="Invalid JSON-stat dataset"):
            flatten_jsonstat_dataset(dataset)


class TestNormalizeTimeToYear:
    """Tests for normalize_time_to_year function."""

    def test_normalize_simple_year(self) -> None:
        """Test normalizing simple year string."""
        assert normalize_time_to_year("2023") == 2023
        assert normalize_time_to_year("2022") == 2022
        assert normalize_time_to_year("1990") == 1990

    def test_normalize_monthly_code(self) -> None:
        """Test normalizing monthly time codes (e.g., 2023M01)."""
        assert normalize_time_to_year("2023M01") == 2023
        assert normalize_time_to_year("2023M12") == 2023
        assert normalize_time_to_year("2022M06") == 2022

    def test_normalize_quarterly_code(self) -> None:
        """Test normalizing quarterly time codes."""
        assert normalize_time_to_year("2023Q1") == 2023
        assert normalize_time_to_year("2023Q4") == 2023

    def test_normalize_from_label(self) -> None:
        """Test normalizing from label when code doesn't contain year."""
        assert normalize_time_to_year(None, "2023") == 2023
        assert normalize_time_to_year("", "2023") == 2023
        assert normalize_time_to_year("invalid", "Year 2023") == 2023

    def test_normalize_none_input(self) -> None:
        """Test normalizing None inputs returns None."""
        assert normalize_time_to_year(None) is None
        assert normalize_time_to_year(None, None) is None

    def test_normalize_invalid_input(self) -> None:
        """Test normalizing invalid input returns None."""
        assert normalize_time_to_year("invalid") is None
        assert normalize_time_to_year("abc", "xyz") is None


class TestNormalizeSex:
    """Tests for normalize_sex function."""

    def test_normalize_male_codes(self) -> None:
        """Test normalizing male codes."""
        assert normalize_sex("M") == "M"
        assert normalize_sex("m") == "M"

    def test_normalize_female_codes(self) -> None:
        """Test normalizing female codes."""
        assert normalize_sex("F") == "F"
        assert normalize_sex("f") == "F"

    def test_normalize_total_codes(self) -> None:
        """Test normalizing total codes."""
        assert normalize_sex("T") == "Total"
        assert normalize_sex("t") == "Total"
        assert normalize_sex("TOTAL") == "Total"
        assert normalize_sex("total") == "Total"

    def test_normalize_from_label(self) -> None:
        """Test normalizing from label."""
        assert normalize_sex(None, "male") == "M"
        assert normalize_sex(None, "Male") == "M"
        assert normalize_sex(None, "men") == "M"
        assert normalize_sex(None, "female") == "F"
        assert normalize_sex(None, "Female") == "F"
        assert normalize_sex(None, "women") == "F"
        assert normalize_sex(None, "total") == "Total"
        assert normalize_sex(None, "both sexes") == "Total"

    def test_normalize_none_input(self) -> None:
        """Test normalizing None inputs returns None."""
        assert normalize_sex(None) is None
        assert normalize_sex(None, None) is None

    def test_normalize_unknown_code(self) -> None:
        """Test normalizing unknown code returns uppercase code."""
        assert normalize_sex("X") == "X"
        assert normalize_sex("unknown") == "UNKNOWN"

    def test_normalize_with_whitespace(self) -> None:
        """Test normalizing with whitespace."""
        assert normalize_sex("  M  ") == "M"
        assert normalize_sex("  F  ") == "F"


class TestNormalizeAge:
    """Tests for normalize_age function."""

    def test_normalize_single_year_code(self) -> None:
        """Test normalizing single year codes (e.g., Y5)."""
        assert normalize_age("Y0") == "0"
        assert normalize_age("Y5") == "5"
        assert normalize_age("Y10") == "10"
        assert normalize_age("Y25") == "25"

    def test_normalize_range_code(self) -> None:
        """Test normalizing range codes (e.g., Y0-4)."""
        assert normalize_age("Y0-4") == "0-4"
        assert normalize_age("Y5-9") == "5-9"
        assert normalize_age("Y10-14") == "10-14"

    def test_normalize_open_ended_code(self) -> None:
        """Test normalizing open-ended codes (e.g., Y_GE85)."""
        assert normalize_age("Y_GE65") == "65+"
        assert normalize_age("Y_GE80") == "80+"
        assert normalize_age("Y_GE85") == "85+"

    def test_normalize_under_code(self) -> None:
        """Test normalizing under codes (e.g., Y_LT5)."""
        assert normalize_age("Y_LT1") == "under 1"
        assert normalize_age("Y_LT5") == "under 5"
        assert normalize_age("Y_LT18") == "under 18"

    def test_normalize_total_code(self) -> None:
        """Test normalizing total codes returns None."""
        assert normalize_age("TOTAL") is None
        assert normalize_age("T") is None
        assert normalize_age("total") is None

    def test_normalize_from_label(self) -> None:
        """Test normalizing from label."""
        assert normalize_age(None, "0-4") == "0-4"
        assert normalize_age(None, "From 0 to 4 years") == "From 0 to 4 years"
        assert normalize_age("", "5-9") == "5-9"

    def test_normalize_none_input(self) -> None:
        """Test normalizing None inputs returns None."""
        assert normalize_age(None) is None
        assert normalize_age(None, None) is None

    def test_normalize_with_whitespace(self) -> None:
        """Test normalizing with whitespace."""
        assert normalize_age("  Y0  ") == "0"
        assert normalize_age("  Y_GE85  ") == "85+"

    def test_normalize_lowercase(self) -> None:
        """Test normalizing lowercase codes."""
        assert normalize_age("y0") == "0"
        assert normalize_age("y_ge85") == "85+"
        assert normalize_age("y_lt5") == "under 5"
