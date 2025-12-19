"""Tests for database repositories."""

from sqlalchemy.orm import Session

from backend.src.database.models import (
    DataSource,
    DemographicData,
    IndustrialData,
    Region,
)
from backend.src.database.repositories import (
    DataSourceRepository,
    DemographicRepository,
    IndustrialRepository,
    RegionRepository,
)


class TestDataSourceRepository:
    """Tests for DataSourceRepository."""

    def test_get_or_create_new(self, test_session: Session) -> None:
        """Test creating a new data source."""
        repo = DataSourceRepository(test_session)
        data_source = repo.get_or_create(
            name="Test Source",
            source_type="csv",
            url="/path/to/file.csv",
            metadata={"version": "1.0"},
        )

        assert data_source.id is not None
        assert data_source.name == "Test Source"
        assert data_source.type == "csv"
        assert data_source.source_metadata == {"version": "1.0"}

    def test_get_or_create_existing(
        self, test_session: Session, sample_data_source: DataSource
    ) -> None:
        """Test getting an existing data source."""
        repo = DataSourceRepository(test_session)
        original_id = sample_data_source.id

        # Get the same source again
        data_source = repo.get_or_create(
            name=sample_data_source.name,
            source_type=sample_data_source.type,
            url=sample_data_source.url,
        )

        assert data_source.id == original_id

    def test_get_or_create_updates_metadata(
        self, test_session: Session, sample_data_source: DataSource
    ) -> None:
        """Test that get_or_create updates metadata on existing source."""
        repo = DataSourceRepository(test_session)
        new_metadata = {"updated": True, "version": "2.0"}

        data_source = repo.get_or_create(
            name=sample_data_source.name,
            source_type=sample_data_source.type,
            url=sample_data_source.url,
            metadata=new_metadata,
        )

        assert data_source.source_metadata == new_metadata

    def test_get_by_id(
        self, test_session: Session, sample_data_source: DataSource
    ) -> None:
        """Test getting data source by ID."""
        repo = DataSourceRepository(test_session)
        data_source = repo.get_by_id(sample_data_source.id)

        assert data_source is not None
        assert data_source.id == sample_data_source.id
        assert data_source.name == sample_data_source.name

    def test_get_by_id_not_found(self, test_session: Session) -> None:
        """Test getting non-existent data source returns None."""
        repo = DataSourceRepository(test_session)
        data_source = repo.get_by_id(99999)

        assert data_source is None

    def test_list_all(
        self, test_session: Session, sample_data_source: DataSource
    ) -> None:
        """Test listing all data sources."""
        repo = DataSourceRepository(test_session)

        # Add another source
        repo.get_or_create(
            name="Another Source",
            source_type="json",
            url="/path/to/file.json",
        )

        sources = repo.list_all()
        assert len(sources) == 2


class TestRegionRepository:
    """Tests for RegionRepository."""

    def test_get_or_create_new(self, test_session: Session) -> None:
        """Test creating a new region."""
        repo = RegionRepository(test_session)
        region = repo.get_or_create(
            code="DE",
            name="Germany",
            level="country",
        )

        assert region.id is not None
        assert region.code == "DE"
        assert region.name == "Germany"
        assert region.level == "country"

    def test_get_or_create_existing(
        self, test_session: Session, sample_region: Region
    ) -> None:
        """Test getting an existing region."""
        repo = RegionRepository(test_session)
        original_id = sample_region.id

        region = repo.get_or_create(
            code=sample_region.code,
            name=sample_region.name,
        )

        assert region.id == original_id

    def test_get_or_create_updates_name(
        self, test_session: Session, sample_region: Region
    ) -> None:
        """Test that get_or_create updates name if changed."""
        repo = RegionRepository(test_session)

        region = repo.get_or_create(
            code=sample_region.code,
            name="Deutschland",  # Updated name
        )

        assert region.name == "Deutschland"

    def test_get_by_code(self, test_session: Session, sample_region: Region) -> None:
        """Test getting region by code."""
        repo = RegionRepository(test_session)
        region = repo.get_by_code("DE")

        assert region is not None
        assert region.code == "DE"

    def test_get_by_code_not_found(self, test_session: Session) -> None:
        """Test getting non-existent region returns None."""
        repo = RegionRepository(test_session)
        region = repo.get_by_code("XX")

        assert region is None

    def test_get_by_id(self, test_session: Session, sample_region: Region) -> None:
        """Test getting region by ID."""
        repo = RegionRepository(test_session)
        region = repo.get_by_id(sample_region.id)

        assert region is not None
        assert region.id == sample_region.id

    def test_list_all(
        self, test_session: Session, sample_regions: list[Region]
    ) -> None:
        """Test listing all regions."""
        repo = RegionRepository(test_session)
        regions = repo.list_all()

        assert len(regions) == len(sample_regions)

    def test_search_by_code(
        self, test_session: Session, sample_regions: list[Region]
    ) -> None:
        """Test searching regions by code."""
        repo = RegionRepository(test_session)
        results = repo.search("DE")

        assert len(results) == 1
        assert results[0].code == "DE"

    def test_search_by_name(
        self, test_session: Session, sample_regions: list[Region]
    ) -> None:
        """Test searching regions by name."""
        repo = RegionRepository(test_session)
        results = repo.search("Germany")

        assert len(results) == 1
        assert results[0].name == "Germany"

    def test_search_partial_match(
        self, test_session: Session, sample_regions: list[Region]
    ) -> None:
        """Test searching regions with partial match."""
        repo = RegionRepository(test_session)
        results = repo.search("an")  # Matches Germany, France, Netherlands

        assert len(results) == 3

    def test_search_no_results(
        self, test_session: Session, sample_regions: list[Region]
    ) -> None:
        """Test searching regions with no matches."""
        repo = RegionRepository(test_session)
        results = repo.search("XYZ")

        assert len(results) == 0


class TestDemographicRepository:
    """Tests for DemographicRepository."""

    def test_bulk_insert(
        self,
        test_session: Session,
        sample_region: Region,
        sample_data_source: DataSource,
    ) -> None:
        """Test bulk inserting demographic records."""
        repo = DemographicRepository(test_session)
        records = [
            {
                "year": 2023,
                "age_min": 0,
                "age_max": 5,
                "gender": "M",
                "population": 1000000,
            },
            {
                "year": 2023,
                "age_min": 0,
                "age_max": 5,
                "gender": "F",
                "population": 950000,
            },
            {
                "year": 2023,
                "age_min": 5,
                "age_max": 10,
                "gender": "M",
                "population": 1100000,
            },
        ]

        count = repo.bulk_insert(records, sample_region.id, sample_data_source.id)

        assert count == 3

    def test_query_all(
        self, test_session: Session, sample_demographic_data: list[DemographicData]
    ) -> None:
        """Test querying all demographic data."""
        repo = DemographicRepository(test_session)
        results = repo.query()

        assert len(results) == len(sample_demographic_data)

    def test_query_by_region_id(
        self,
        test_session: Session,
        sample_demographic_data: list[DemographicData],
        sample_region: Region,
    ) -> None:
        """Test querying by region ID."""
        repo = DemographicRepository(test_session)
        results = repo.query(region_id=sample_region.id)

        assert len(results) == len(sample_demographic_data)

    def test_query_by_region_code(
        self,
        test_session: Session,
        sample_demographic_data: list[DemographicData],
    ) -> None:
        """Test querying by region code."""
        repo = DemographicRepository(test_session)
        results = repo.query(region_code="DE")

        assert len(results) == len(sample_demographic_data)

    def test_query_by_year(
        self, test_session: Session, sample_demographic_data: list[DemographicData]
    ) -> None:
        """Test querying by year."""
        repo = DemographicRepository(test_session)
        results = repo.query(year=2023)

        assert len(results) == 3  # Only 2023 records

    def test_query_by_gender(
        self, test_session: Session, sample_demographic_data: list[DemographicData]
    ) -> None:
        """Test querying by gender."""
        repo = DemographicRepository(test_session)
        results = repo.query(gender="M")

        assert len(results) == 2  # Two male records

    def test_query_with_limit(
        self, test_session: Session, sample_demographic_data: list[DemographicData]
    ) -> None:
        """Test querying with limit."""
        repo = DemographicRepository(test_session)
        results = repo.query(limit=2)

        assert len(results) == 2

    def test_get_statistics(
        self, test_session: Session, sample_demographic_data: list[DemographicData]
    ) -> None:
        """Test getting demographic statistics."""
        repo = DemographicRepository(test_session)
        stats = repo.get_statistics()

        assert stats["total_records"] == len(sample_demographic_data)
        assert "years_covered" in stats

    def test_get_statistics_by_region(
        self,
        test_session: Session,
        sample_demographic_data: list[DemographicData],
        sample_region: Region,
    ) -> None:
        """Test getting statistics filtered by region."""
        repo = DemographicRepository(test_session)
        stats = repo.get_statistics(region_id=sample_region.id)

        assert stats["total_records"] == len(sample_demographic_data)

    def test_delete_by_source(
        self,
        test_session: Session,
        sample_demographic_data: list[DemographicData],
        sample_data_source: DataSource,
    ) -> None:
        """Test deleting demographic data by source."""
        repo = DemographicRepository(test_session)
        deleted_count = repo.delete_by_source(sample_data_source.id)

        assert deleted_count == len(sample_demographic_data)

        # Verify data is deleted
        remaining = repo.query()
        assert len(remaining) == 0


class TestIndustrialRepository:
    """Tests for IndustrialRepository."""

    def test_bulk_insert(
        self,
        test_session: Session,
        sample_region: Region,
        sample_data_source: DataSource,
    ) -> None:
        """Test bulk inserting industrial records."""
        repo = IndustrialRepository(test_session)
        records = [
            {
                "year": 2023,
                "month": 10,
                "nace_code": "B-D",
                "index_value": 98,
                "unit": "I15",
            },
            {
                "year": 2023,
                "month": 11,
                "nace_code": "B-D",
                "index_value": 97,
                "unit": "I15",
            },
        ]

        count = repo.bulk_insert(records, sample_region.id, sample_data_source.id)

        assert count == 2

    def test_query_all(
        self, test_session: Session, sample_industrial_data: list[IndustrialData]
    ) -> None:
        """Test querying all industrial data."""
        repo = IndustrialRepository(test_session)
        results = repo.query()

        assert len(results) == len(sample_industrial_data)

    def test_query_by_region_id(
        self,
        test_session: Session,
        sample_industrial_data: list[IndustrialData],
        sample_region: Region,
    ) -> None:
        """Test querying by region ID."""
        repo = IndustrialRepository(test_session)
        results = repo.query(region_id=sample_region.id)

        assert len(results) == len(sample_industrial_data)

    def test_query_by_region_code(
        self, test_session: Session, sample_industrial_data: list[IndustrialData]
    ) -> None:
        """Test querying by region code."""
        repo = IndustrialRepository(test_session)
        results = repo.query(region_code="DE")

        assert len(results) == len(sample_industrial_data)

    def test_query_by_year(
        self, test_session: Session, sample_industrial_data: list[IndustrialData]
    ) -> None:
        """Test querying by year."""
        repo = IndustrialRepository(test_session)
        results = repo.query(year=2023)

        assert len(results) == len(sample_industrial_data)

    def test_query_by_month(
        self, test_session: Session, sample_industrial_data: list[IndustrialData]
    ) -> None:
        """Test querying by month."""
        repo = IndustrialRepository(test_session)
        results = repo.query(month=10)

        assert len(results) == 1

    def test_query_by_nace_code(
        self, test_session: Session, sample_industrial_data: list[IndustrialData]
    ) -> None:
        """Test querying by NACE code."""
        repo = IndustrialRepository(test_session)
        results = repo.query(nace_code="B-D")

        assert len(results) == 2

    def test_query_ordered_by_date(
        self, test_session: Session, sample_industrial_data: list[IndustrialData]
    ) -> None:
        """Test that results are ordered by year and month descending."""
        repo = IndustrialRepository(test_session)
        results = repo.query()

        # Should be ordered newest first
        assert results[0].month == 12
        assert results[1].month == 11
        assert results[2].month == 10

    def test_query_with_limit(
        self, test_session: Session, sample_industrial_data: list[IndustrialData]
    ) -> None:
        """Test querying with limit."""
        repo = IndustrialRepository(test_session)
        results = repo.query(limit=1)

        assert len(results) == 1

    def test_get_statistics(
        self, test_session: Session, sample_industrial_data: list[IndustrialData]
    ) -> None:
        """Test getting industrial statistics."""
        repo = IndustrialRepository(test_session)
        stats = repo.get_statistics()

        assert stats["total_records"] == len(sample_industrial_data)
        assert "years_covered" in stats
        assert "nace_codes" in stats
        assert set(stats["nace_codes"]) == {"B-D", "C"}

    def test_delete_by_source(
        self,
        test_session: Session,
        sample_industrial_data: list[IndustrialData],
        sample_data_source: DataSource,
    ) -> None:
        """Test deleting industrial data by source."""
        repo = IndustrialRepository(test_session)
        deleted_count = repo.delete_by_source(sample_data_source.id)

        assert deleted_count == len(sample_industrial_data)

        # Verify data is deleted
        remaining = repo.query()
        assert len(remaining) == 0
