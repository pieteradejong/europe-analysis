"""Integration tests for database operations."""

from typing import Any

import pytest
from sqlalchemy.orm import Session, sessionmaker

from backend.src.database.base import Base
from backend.src.database.models import (
    DataSource,
    DemographicData,
    Region,
)
from backend.src.database.repositories import (
    DataSourceRepository,
    DemographicRepository,
    IndustrialRepository,
    RegionRepository,
)


class TestDatabaseEngine:
    """Tests for database engine creation."""

    def test_sqlite_engine_creation(self, test_engine: Any) -> None:
        """Test SQLite engine is created correctly."""
        assert test_engine is not None
        assert "sqlite" in str(test_engine.url)

    def test_tables_created(self, test_engine: Any) -> None:
        """Test that all tables are created."""
        table_names = Base.metadata.tables.keys()

        # Core tables
        assert "data_sources" in table_names
        assert "regions" in table_names
        assert "demographic_data" in table_names
        assert "industrial_data" in table_names

        # GICPT tables
        assert "capacity_utilization" in table_names
        assert "manufacturing_orders" in table_names
        assert "energy_consumption" in table_names
        assert "labor_market_data" in table_names
        assert "computed_metrics" in table_names


class TestSessionManagement:
    """Tests for database session management."""

    def test_session_commit(self, test_session: Session) -> None:
        """Test session commits successfully."""
        region = Region(code="TEST", name="Test Region", level="country")
        test_session.add(region)
        test_session.flush()

        # Query to verify
        result = test_session.query(Region).filter(Region.code == "TEST").first()
        assert result is not None
        assert result.name == "Test Region"

    def test_session_rollback_on_error(self, test_engine: Any) -> None:
        """Test session rollback on error."""
        from sqlalchemy.exc import IntegrityError

        session_factory = sessionmaker(bind=test_engine)
        session = session_factory()

        try:
            # Create a region
            region = Region(code="RB", name="Rollback Test", level="country")
            session.add(region)
            session.flush()

            # Try to create duplicate (should fail on unique constraint)
            duplicate = Region(code="RB", name="Duplicate", level="country")
            session.add(duplicate)

            with pytest.raises(IntegrityError):
                session.flush()

            session.rollback()

            # After rollback, the original should not be committed
            new_session = session_factory()
            result = new_session.query(Region).filter(Region.code == "RB").first()
            assert result is None
            new_session.close()
        finally:
            session.close()


class TestForeignKeyConstraints:
    """Tests for foreign key constraints."""

    def test_foreign_key_enforced(
        self, test_session: Session, sample_data_source: DataSource
    ) -> None:
        """Test that foreign key constraints are enforced."""
        from sqlalchemy.exc import IntegrityError

        # Try to create demographic data with non-existent region
        demo_data = DemographicData(
            region_id=99999,  # Non-existent
            data_source_id=sample_data_source.id,
            year=2023,
            gender="M",
            population=1000000,
        )
        test_session.add(demo_data)

        with pytest.raises(IntegrityError):
            test_session.flush()

    def test_cascade_relationships(
        self,
        test_session: Session,
        sample_region: Region,
        sample_data_source: DataSource,
    ) -> None:
        """Test relationship navigation works correctly."""
        # Create demographic data
        demo_data = DemographicData(
            region_id=sample_region.id,
            data_source_id=sample_data_source.id,
            year=2023,
            gender="M",
            population=1000000,
        )
        test_session.add(demo_data)
        test_session.flush()

        # Navigate relationship
        assert demo_data.region == sample_region
        assert demo_data.data_source == sample_data_source
        assert demo_data in sample_region.demographic_data


class TestTransactions:
    """Tests for transaction handling."""

    def test_multiple_operations_in_transaction(
        self, test_session: Session, sample_data_source: DataSource
    ) -> None:
        """Test multiple operations in a single transaction."""
        # Create multiple related records
        region = Region(code="TX", name="Transaction Test", level="country")
        test_session.add(region)
        test_session.flush()

        demo1 = DemographicData(
            region_id=region.id,
            data_source_id=sample_data_source.id,
            year=2023,
            gender="M",
            population=500000,
        )
        demo2 = DemographicData(
            region_id=region.id,
            data_source_id=sample_data_source.id,
            year=2023,
            gender="F",
            population=520000,
        )
        test_session.add_all([demo1, demo2])
        test_session.flush()

        # Verify both records exist
        results = (
            test_session.query(DemographicData)
            .filter(DemographicData.region_id == region.id)
            .all()
        )
        assert len(results) == 2


class TestFullWorkflow:
    """Integration tests for complete data workflows."""

    def test_data_acquisition_workflow(self, test_session: Session) -> None:
        """Test complete data acquisition workflow."""
        # 1. Create data source
        source_repo = DataSourceRepository(test_session)
        data_source = source_repo.get_or_create(
            name="Eurostat Population",
            source_type="api",
            url="https://ec.europa.eu/eurostat/api/data/demo_pjan",
            metadata={"dataset_id": "demo_pjan", "params": {"geo": "DE"}},
        )

        # 2. Create region
        region_repo = RegionRepository(test_session)
        region = region_repo.get_or_create(
            code="DE",
            name="Germany",
            level="country",
        )

        # 3. Insert demographic data
        demo_repo = DemographicRepository(test_session)
        records = [
            {
                "year": 2023,
                "age_min": 0,
                "age_max": 5,
                "gender": "M",
                "population": 2000000,
            },
            {
                "year": 2023,
                "age_min": 0,
                "age_max": 5,
                "gender": "F",
                "population": 1900000,
            },
            {
                "year": 2023,
                "age_min": 5,
                "age_max": 10,
                "gender": "M",
                "population": 2100000,
            },
            {
                "year": 2023,
                "age_min": 5,
                "age_max": 10,
                "gender": "F",
                "population": 2000000,
            },
        ]
        count = demo_repo.bulk_insert(records, region.id, data_source.id)
        assert count == 4

        # 4. Query data back
        results = demo_repo.query(region_code="DE", year=2023)
        assert len(results) == 4

        # 5. Get statistics
        stats = demo_repo.get_statistics(region_id=region.id)
        assert stats["total_records"] == 4

    def test_industrial_data_workflow(self, test_session: Session) -> None:
        """Test complete industrial data workflow."""
        # 1. Create data source
        source_repo = DataSourceRepository(test_session)
        data_source = source_repo.get_or_create(
            name="Eurostat Industrial Production",
            source_type="api",
            url="https://ec.europa.eu/eurostat/api/data/sts_inpr_m",
        )

        # 2. Create region
        region_repo = RegionRepository(test_session)
        region = region_repo.get_or_create(
            code="DE",
            name="Germany",
            level="country",
        )

        # 3. Insert industrial data
        industrial_repo = IndustrialRepository(test_session)
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
            {
                "year": 2023,
                "month": 12,
                "nace_code": "B-D",
                "index_value": 96,
                "unit": "I15",
            },
        ]
        count = industrial_repo.bulk_insert(records, region.id, data_source.id)
        assert count == 3

        # 4. Query data back (should be ordered by date descending)
        results = industrial_repo.query(region_code="DE")
        assert len(results) == 3
        assert results[0].month == 12  # Most recent first

        # 5. Get statistics
        stats = industrial_repo.get_statistics()
        assert stats["total_records"] == 3
        assert "B-D" in stats["nace_codes"]

    def test_hierarchical_regions(self, test_session: Session) -> None:
        """Test hierarchical region relationships."""
        region_repo = RegionRepository(test_session)

        # Create country
        germany = region_repo.get_or_create(
            code="DE",
            name="Germany",
            level="country",
        )

        # Create NUTS1 regions
        bavaria = region_repo.get_or_create(
            code="DE2",
            name="Bavaria",
            level="nuts1",
            parent_region_id=germany.id,
        )
        nrw = region_repo.get_or_create(
            code="DE7",
            name="North Rhine-Westphalia",
            level="nuts1",
            parent_region_id=germany.id,
        )

        # Verify hierarchy
        assert bavaria.parent_region == germany
        assert nrw.parent_region == germany
        assert bavaria in germany.sub_regions
        assert nrw in germany.sub_regions

    def test_data_cleanup_workflow(
        self, test_session: Session, sample_demographic_data: list[DemographicData]
    ) -> None:
        """Test data cleanup workflow."""
        demo_repo = DemographicRepository(test_session)
        data_source_id = sample_demographic_data[0].data_source_id

        # Verify data exists
        initial_count = len(demo_repo.query())
        assert initial_count == len(sample_demographic_data)

        # Delete by source
        deleted = demo_repo.delete_by_source(data_source_id)
        assert deleted == len(sample_demographic_data)

        # Verify data is gone
        remaining = demo_repo.query()
        assert len(remaining) == 0
