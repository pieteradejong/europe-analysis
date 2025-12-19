"""End-to-end tests for complete data pipeline flows."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import (
    create_engine as sa_create_engine,
    event,
)
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.src.data_acquisition.eurostat.acquirer import EurostatAcquirer
from backend.src.data_acquisition.eurostat.jsonstat import flatten_jsonstat_dataset
from backend.src.data_acquisition.normalizer import DemographicNormalizer
from backend.src.database.base import Base
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


class TestFullDemographicPipeline:
    """End-to-end tests for demographic data pipeline."""

    @pytest.fixture
    def e2e_engine(self) -> Any:
        """Create a fresh engine for E2E tests."""
        engine = sa_create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn: Any, connection_record: Any) -> None:
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        Base.metadata.create_all(engine)
        yield engine
        Base.metadata.drop_all(engine)
        engine.dispose()

    @pytest.fixture
    def e2e_session(self, e2e_engine: Any) -> Session:
        """Create a session for E2E tests."""
        session_factory = sessionmaker(bind=e2e_engine)
        session = session_factory()
        yield session
        session.close()

    def test_full_demographic_data_flow(
        self,
        e2e_session: Session,
        mock_eurostat_jsonstat_response: dict[str, Any],
    ) -> None:
        """Test complete demographic data flow from acquisition to query."""
        # Step 1: Simulate Eurostat API response
        with patch(
            "backend.src.data_acquisition.eurostat.acquirer.EurostatClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.get_dataset.return_value = mock_eurostat_jsonstat_response
            mock_client_class.return_value = mock_client

            # Step 2: Acquire data
            acquirer = EurostatAcquirer(
                source="demo_pjan",
                params={"geo": "DE,FR", "time": "2022,2023"},
            )
            result = acquirer.acquire()

            assert result.success is True
            assert len(result.data) > 0

        # Step 3: Normalize data
        normalizer = DemographicNormalizer()
        normalized_records = []
        for record in result.data:
            normalized = normalizer.normalize_record(record)
            if normalized:
                normalized_records.append(normalized)

        assert len(normalized_records) > 0

        # Step 4: Create data source
        source_repo = DataSourceRepository(e2e_session)
        data_source = source_repo.get_or_create(
            name="Eurostat Population Test",
            source_type="api",
            url="https://ec.europa.eu/eurostat/api/data/demo_pjan",
            metadata={"dataset_id": "demo_pjan"},
        )

        # Step 5: Create regions
        region_repo = RegionRepository(e2e_session)
        regions_created = {}
        for record in normalized_records:
            region_code = record["region_code"]
            if region_code not in regions_created:
                region = region_repo.get_or_create(
                    code=region_code,
                    name=record.get("region_name", region_code),
                    level="country",
                )
                regions_created[region_code] = region

        # Step 6: Insert demographic data
        demo_repo = DemographicRepository(e2e_session)
        for record in normalized_records:
            region = regions_created[record["region_code"]]
            demo_data = DemographicData(
                region_id=region.id,
                data_source_id=data_source.id,
                year=record.get("year"),
                age_min=record.get("age_min"),
                age_max=record.get("age_max"),
                gender=record.get("gender", "Total"),
                population=record.get("population", 0),
            )
            e2e_session.add(demo_data)
        e2e_session.flush()

        # Step 7: Query data back
        germany_data = demo_repo.query(region_code="DE")
        france_data = demo_repo.query(region_code="FR")

        assert len(germany_data) > 0
        assert len(france_data) > 0

        # Step 8: Verify data integrity
        stats = demo_repo.get_statistics()
        assert stats["total_records"] == len(normalized_records)

        # Step 9: Query with filters
        male_data = demo_repo.query(gender="M")
        assert all(d.gender == "M" for d in male_data)

        data_2023 = demo_repo.query(year=2023)
        assert all(d.year == 2023 for d in data_2023)

    def test_full_industrial_data_flow(
        self,
        e2e_session: Session,
        mock_eurostat_industrial_response: dict[str, Any],
    ) -> None:
        """Test complete industrial data flow from acquisition to query."""
        # Step 1: Parse JSON-stat data
        flattened = flatten_jsonstat_dataset(mock_eurostat_industrial_response)
        assert len(flattened) == 3  # 3 months of data

        # Step 2: Create data source
        source_repo = DataSourceRepository(e2e_session)
        data_source = source_repo.get_or_create(
            name="Eurostat Industrial Production Test",
            source_type="api",
            url="https://ec.europa.eu/eurostat/api/data/sts_inpr_m",
        )

        # Step 3: Create region
        region_repo = RegionRepository(e2e_session)
        germany = region_repo.get_or_create(
            code="DE",
            name="Germany",
            level="country",
        )

        # Step 4: Insert industrial data
        industrial_repo = IndustrialRepository(e2e_session)
        for record in flattened:
            time_code = record.get("time", "")
            # Parse time (e.g., "2023M10" -> year=2023, month=10)
            year = int(time_code[:4]) if len(time_code) >= 4 else None
            month = (
                int(time_code[5:7])
                if len(time_code) >= 7 and time_code[4] == "M"
                else None
            )

            industrial = IndustrialData(
                region_id=germany.id,
                data_source_id=data_source.id,
                year=year,
                month=month,
                nace_code=record.get("nace_r2"),
                index_value=int(record.get("value", 0)),
                unit=record.get("unit"),
            )
            e2e_session.add(industrial)
        e2e_session.flush()

        # Step 5: Query data back
        results = industrial_repo.query(region_code="DE")
        assert len(results) == 3

        # Step 6: Verify ordering (newest first)
        assert results[0].month == 12
        assert results[1].month == 11
        assert results[2].month == 10

        # Step 7: Get statistics
        stats = industrial_repo.get_statistics()
        assert stats["total_records"] == 3
        assert "B-D" in stats["nace_codes"]


class TestDataIntegrity:
    """Tests for data integrity across the pipeline."""

    def test_population_values_preserved(
        self, test_session: Session, mock_eurostat_jsonstat_response: dict[str, Any]
    ) -> None:
        """Test that population values are preserved through the pipeline."""
        # Flatten JSON-stat
        flattened = flatten_jsonstat_dataset(mock_eurostat_jsonstat_response)

        # Get original values for DE, 2023, M, Y0-4
        original_value = None
        for record in flattened:
            if (
                record.get("geo") == "DE"
                and record.get("time") == "2023"
                and record.get("sex") == "M"
                and record.get("age") == "Y0-4"
            ):
                original_value = record.get("value")
                break

        assert original_value is not None
        assert original_value == 1980000  # From mock data

    def test_region_codes_preserved(
        self, mock_eurostat_jsonstat_response: dict[str, Any]
    ) -> None:
        """Test that region codes are preserved through normalization."""
        flattened = flatten_jsonstat_dataset(mock_eurostat_jsonstat_response)
        normalizer = DemographicNormalizer()

        region_codes = set()
        for record in flattened:
            # Map to normalized format
            normalized_record = {
                "region_code": record.get("geo"),
                "region_name": record.get("geo__label"),
                "year": record.get("time"),
                "gender": record.get("sex"),
                "population": record.get("value"),
            }
            normalized = normalizer.normalize_record(normalized_record)
            if normalized:
                region_codes.add(normalized["region_code"])

        assert "DE" in region_codes
        assert "FR" in region_codes


class TestErrorRecovery:
    """Tests for error handling and recovery in the pipeline."""

    def test_partial_data_handling(
        self, test_session: Session, sample_data_source: DataSource
    ) -> None:
        """Test handling of partial data (some records invalid)."""
        normalizer = DemographicNormalizer()

        # Mix of valid and invalid records
        records = [
            {"region_code": "DE", "year": 2023, "gender": "M", "population": 1000000},
            {"year": 2023, "gender": "F", "population": 950000},  # Missing region
            {"region_code": "FR", "year": 2023, "gender": "M"},  # Missing population
            {"region_code": "IT", "year": 2023, "gender": "F", "population": 800000},
        ]

        normalized = normalizer.normalize_batch(records)

        # Only 2 valid records should be processed
        assert len(normalized) == 2
        codes = {r["region_code"] for r in normalized}
        assert codes == {"DE", "IT"}

    def test_duplicate_region_handling(self, test_session: Session) -> None:
        """Test handling of duplicate region codes."""
        region_repo = RegionRepository(test_session)

        # Create region
        region1 = region_repo.get_or_create(
            code="DE",
            name="Germany",
            level="country",
        )
        region_id1 = region1.id

        # Try to create same region again
        region2 = region_repo.get_or_create(
            code="DE",
            name="Deutschland",  # Different name
            level="country",
        )

        # Should return same region (updated name)
        assert region2.id == region_id1
        assert region2.name == "Deutschland"


class TestDataRefresh:
    """Tests for data refresh workflows."""

    def test_delete_and_reacquire(
        self,
        test_session: Session,
        sample_demographic_data: list[DemographicData],
        sample_data_source: DataSource,
        sample_region: Region,
    ) -> None:
        """Test deleting old data and re-acquiring."""
        demo_repo = DemographicRepository(test_session)

        # Verify initial data exists
        initial_count = len(demo_repo.query())
        assert initial_count == len(sample_demographic_data)

        # Delete old data
        deleted = demo_repo.delete_by_source(sample_data_source.id)
        assert deleted == len(sample_demographic_data)

        # Verify deletion
        remaining = demo_repo.query()
        assert len(remaining) == 0

        # Re-insert new data
        new_records = [
            {
                "year": 2024,
                "age_min": 0,
                "age_max": 5,
                "gender": "M",
                "population": 2100000,
            },
            {
                "year": 2024,
                "age_min": 0,
                "age_max": 5,
                "gender": "F",
                "population": 2000000,
            },
        ]
        count = demo_repo.bulk_insert(
            new_records, sample_region.id, sample_data_source.id
        )
        assert count == 2

        # Verify new data
        final_data = demo_repo.query()
        assert len(final_data) == 2
        assert all(d.year == 2024 for d in final_data)
