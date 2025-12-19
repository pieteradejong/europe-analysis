"""Tests for DemographicNormalizer."""

from backend.src.data_acquisition.normalizer import DemographicNormalizer


class TestNormalizeGender:
    """Tests for gender normalization."""

    def test_normalize_male_variants(self) -> None:
        """Test normalizing various male representations."""
        normalizer = DemographicNormalizer()

        assert normalizer.normalize_gender("m") == "M"
        assert normalizer.normalize_gender("M") == "M"
        assert normalizer.normalize_gender("male") == "M"
        assert normalizer.normalize_gender("Male") == "M"
        assert normalizer.normalize_gender("MALE") == "M"
        assert normalizer.normalize_gender("masculine") == "M"

    def test_normalize_female_variants(self) -> None:
        """Test normalizing various female representations."""
        normalizer = DemographicNormalizer()

        assert normalizer.normalize_gender("f") == "F"
        assert normalizer.normalize_gender("F") == "F"
        assert normalizer.normalize_gender("female") == "F"
        assert normalizer.normalize_gender("Female") == "F"
        assert normalizer.normalize_gender("FEMALE") == "F"
        assert normalizer.normalize_gender("feminine") == "F"

    def test_normalize_total_variants(self) -> None:
        """Test normalizing total/both representations."""
        normalizer = DemographicNormalizer()

        assert normalizer.normalize_gender("t") == "Total"
        assert normalizer.normalize_gender("T") == "Total"
        assert normalizer.normalize_gender("total") == "Total"
        assert normalizer.normalize_gender("Total") == "Total"
        assert normalizer.normalize_gender("all") == "Total"
        assert normalizer.normalize_gender("both") == "Total"

    def test_normalize_other_variants(self) -> None:
        """Test normalizing other/unknown representations."""
        normalizer = DemographicNormalizer()

        assert normalizer.normalize_gender("o") == "O"
        assert normalizer.normalize_gender("other") == "O"
        assert normalizer.normalize_gender("unknown") == "O"
        assert normalizer.normalize_gender("unspecified") == "O"

    def test_normalize_gender_none(self) -> None:
        """Test normalizing None returns None."""
        normalizer = DemographicNormalizer()

        assert normalizer.normalize_gender(None) is None

    def test_normalize_gender_whitespace(self) -> None:
        """Test normalizing gender with whitespace."""
        normalizer = DemographicNormalizer()

        assert normalizer.normalize_gender("  m  ") == "M"
        assert normalizer.normalize_gender("\tfemale\n") == "F"

    def test_normalize_unknown_gender(self) -> None:
        """Test normalizing unknown gender returns uppercase."""
        normalizer = DemographicNormalizer()

        assert normalizer.normalize_gender("xyz") == "XYZ"


class TestParseAgeGroup:
    """Tests for age group parsing."""

    def test_parse_range_hyphen(self) -> None:
        """Test parsing age range with hyphen (e.g., '0-4')."""
        normalizer = DemographicNormalizer()

        assert normalizer.parse_age_group("0-4") == (0, 5)
        assert normalizer.parse_age_group("5-9") == (5, 10)
        assert normalizer.parse_age_group("10-14") == (10, 15)
        assert normalizer.parse_age_group("80-84") == (80, 85)

    def test_parse_range_with_spaces(self) -> None:
        """Test parsing age range with spaces."""
        normalizer = DemographicNormalizer()

        assert normalizer.parse_age_group("0 - 4") == (0, 5)
        assert normalizer.parse_age_group("5  -  9") == (5, 10)

    def test_parse_range_to(self) -> None:
        """Test parsing age range with 'to' (e.g., '0 to 4')."""
        normalizer = DemographicNormalizer()

        assert normalizer.parse_age_group("0 to 4") == (0, 5)
        assert normalizer.parse_age_group("5 to 9") == (5, 10)

    def test_parse_open_ended(self) -> None:
        """Test parsing open-ended age groups (e.g., '65+')."""
        normalizer = DemographicNormalizer()

        assert normalizer.parse_age_group("65+") == (65, None)
        assert normalizer.parse_age_group("80+") == (80, None)
        assert normalizer.parse_age_group("85+") == (85, None)

    def test_parse_under(self) -> None:
        """Test parsing 'under X' age groups."""
        normalizer = DemographicNormalizer()

        assert normalizer.parse_age_group("under 5") == (0, 5)
        assert normalizer.parse_age_group("under 1") == (0, 1)
        assert normalizer.parse_age_group("under 18") == (0, 18)

    def test_parse_over(self) -> None:
        """Test parsing 'over X' age groups."""
        normalizer = DemographicNormalizer()

        assert normalizer.parse_age_group("over 65") == (65, None)
        assert normalizer.parse_age_group("over 80") == (80, None)

    def test_parse_single_age(self) -> None:
        """Test parsing single age values."""
        normalizer = DemographicNormalizer()

        assert normalizer.parse_age_group("0") == (0, 1)
        assert normalizer.parse_age_group("5") == (5, 6)
        assert normalizer.parse_age_group("25") == (25, 26)

    def test_parse_age_none(self) -> None:
        """Test parsing None returns (None, None)."""
        normalizer = DemographicNormalizer()

        assert normalizer.parse_age_group(None) == (None, None)

    def test_parse_age_integer_input(self) -> None:
        """Test parsing integer input."""
        normalizer = DemographicNormalizer()

        assert normalizer.parse_age_group(5) == (5, 6)
        assert normalizer.parse_age_group(0) == (0, 1)

    def test_parse_age_with_text(self) -> None:
        """Test parsing age groups with additional text."""
        normalizer = DemographicNormalizer()

        # Should extract numbers
        assert normalizer.parse_age_group("Age 5-9 years") == (5, 10)
        assert normalizer.parse_age_group("From 0 to 4 years") == (0, 5)


class TestNormalizeRecord:
    """Tests for record normalization."""

    def test_normalize_complete_record(self) -> None:
        """Test normalizing a complete record with all fields."""
        normalizer = DemographicNormalizer()
        record = {
            "region_code": "DE",
            "region_name": "Germany",
            "year": 2023,
            "age_group": "0-4",
            "gender": "M",
            "population": 1000000,
        }

        result = normalizer.normalize_record(record)

        assert result is not None
        assert result["region_code"] == "DE"
        assert result["region_name"] == "Germany"
        assert result["year"] == 2023
        assert result["age_min"] == 0
        assert result["age_max"] == 5
        assert result["gender"] == "M"
        assert result["population"] == 1000000

    def test_normalize_record_with_field_mapping(self) -> None:
        """Test normalizing a record with field mapping."""
        normalizer = DemographicNormalizer()
        record = {
            "country_code": "DE",
            "country_name": "Germany",
            "data_year": 2023,
            "age": "0-4",
            "sex": "male",
            "pop": 1000000,
        }
        field_mapping = {
            "country_code": "region_code",
            "country_name": "region_name",
            "data_year": "year",
            "age": "age_group",
            "sex": "gender",
            "pop": "population",
        }

        result = normalizer.normalize_record(record, field_mapping)

        assert result is not None
        assert result["region_code"] == "DE"
        assert result["year"] == 2023
        assert result["gender"] == "M"

    def test_normalize_record_missing_region(self) -> None:
        """Test normalizing a record with missing region returns None."""
        normalizer = DemographicNormalizer()
        record = {
            "year": 2023,
            "gender": "M",
            "population": 1000000,
        }

        result = normalizer.normalize_record(record)

        assert result is None

    def test_normalize_record_missing_population(self) -> None:
        """Test normalizing a record with missing population returns None."""
        normalizer = DemographicNormalizer()
        record = {
            "region_code": "DE",
            "year": 2023,
            "gender": "M",
        }

        result = normalizer.normalize_record(record)

        assert result is None

    def test_normalize_record_alternative_field_names(self) -> None:
        """Test normalizing a record with alternative field names."""
        normalizer = DemographicNormalizer()
        record = {
            "code": "DE",
            "name": "Germany",
            "date": "2023",
            "sex": "female",
            "value": 950000,
        }

        result = normalizer.normalize_record(record)

        assert result is not None
        assert result["region_code"] == "DE"
        assert result["year"] == 2023
        assert result["gender"] == "F"
        assert result["population"] == 950000

    def test_normalize_record_year_from_date_string(self) -> None:
        """Test extracting year from date string."""
        normalizer = DemographicNormalizer()
        record = {
            "region_code": "DE",
            "date": "2023-01-01",
            "gender": "M",
            "population": 1000000,
        }

        result = normalizer.normalize_record(record)

        assert result is not None
        assert result["year"] == 2023

    def test_normalize_record_population_as_float(self) -> None:
        """Test normalizing population value given as float."""
        normalizer = DemographicNormalizer()
        record = {
            "region_code": "DE",
            "year": 2023,
            "gender": "M",
            "population": 1000000.5,
        }

        result = normalizer.normalize_record(record)

        assert result is not None
        assert result["population"] == 1000000

    def test_normalize_record_population_as_string(self) -> None:
        """Test normalizing population value given as string."""
        normalizer = DemographicNormalizer()
        record = {
            "region_code": "DE",
            "year": 2023,
            "gender": "M",
            "population": "1000000",
        }

        result = normalizer.normalize_record(record)

        assert result is not None
        assert result["population"] == 1000000

    def test_normalize_record_default_gender(self) -> None:
        """Test that gender defaults to 'Total' if not specified."""
        normalizer = DemographicNormalizer()
        record = {
            "region_code": "DE",
            "year": 2023,
            "population": 1000000,
        }

        result = normalizer.normalize_record(record)

        assert result is not None
        assert result["gender"] == "Total"

    def test_normalize_record_split_gender(self) -> None:
        """Test record with separate male/female columns."""
        normalizer = DemographicNormalizer()
        record = {
            "region_code": "DE",
            "year": 2023,
            "male": 1000000,
            "female": 950000,
            "population": 1950000,
        }

        result = normalizer.normalize_record(record)

        assert result is not None
        assert result.get("_split_gender") is True
        assert result["_male_pop"] == 1000000
        assert result["_female_pop"] == 950000


class TestNormalizeBatch:
    """Tests for batch normalization."""

    def test_normalize_batch_simple(self) -> None:
        """Test normalizing a batch of simple records."""
        normalizer = DemographicNormalizer()
        records = [
            {"region_code": "DE", "year": 2023, "gender": "M", "population": 1000000},
            {"region_code": "DE", "year": 2023, "gender": "F", "population": 950000},
            {"region_code": "FR", "year": 2023, "gender": "M", "population": 900000},
        ]

        results = normalizer.normalize_batch(records)

        assert len(results) == 3

    def test_normalize_batch_with_split_gender(self) -> None:
        """Test normalizing batch with records that need gender splitting."""
        normalizer = DemographicNormalizer()
        records = [
            {
                "region_code": "DE",
                "year": 2023,
                "male": 1000000,
                "female": 950000,
                "population": 1950000,
            },
        ]

        results = normalizer.normalize_batch(records)

        # Should have 2 records: one male, one female
        assert len(results) == 2
        male_record = next(r for r in results if r["gender"] == "M")
        female_record = next(r for r in results if r["gender"] == "F")
        assert male_record["population"] == 1000000
        assert female_record["population"] == 950000

    def test_normalize_batch_filters_invalid(self) -> None:
        """Test that invalid records are filtered from batch."""
        normalizer = DemographicNormalizer()
        records = [
            {"region_code": "DE", "year": 2023, "gender": "M", "population": 1000000},
            {"year": 2023, "gender": "F", "population": 950000},  # Missing region
            {"region_code": "FR", "year": 2023, "gender": "M"},  # Missing population
        ]

        results = normalizer.normalize_batch(records)

        assert len(results) == 1
        assert results[0]["region_code"] == "DE"

    def test_normalize_batch_with_field_mapping(self) -> None:
        """Test normalizing batch with field mapping."""
        normalizer = DemographicNormalizer()
        records = [
            {"code": "DE", "yr": 2023, "pop": 1000000},
            {"code": "FR", "yr": 2023, "pop": 900000},
        ]
        field_mapping = {
            "code": "region_code",
            "yr": "year",
            "pop": "population",
        }

        results = normalizer.normalize_batch(records, field_mapping)

        assert len(results) == 2
        assert results[0]["region_code"] == "DE"
        assert results[1]["region_code"] == "FR"

    def test_normalize_batch_empty_input(self) -> None:
        """Test normalizing empty batch returns empty list."""
        normalizer = DemographicNormalizer()

        results = normalizer.normalize_batch([])

        assert results == []

    def test_normalize_batch_preserves_original(self) -> None:
        """Test that original record is preserved in _original field."""
        normalizer = DemographicNormalizer()
        records = [
            {
                "region_code": "DE",
                "year": 2023,
                "gender": "M",
                "population": 1000000,
                "extra": "data",
            },
        ]

        results = normalizer.normalize_batch(records)

        assert len(results) == 1
        assert results[0]["_original"]["extra"] == "data"
