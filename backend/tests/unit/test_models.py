"""Tests for database models."""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.src.database.models import (
    CapacityUtilization,
    ComputedMetric,
    DataSource,
    DemographicData,
    EnergyConsumption,
    IndustrialData,
    LaborMarketData,
    ManufacturingOrders,
    Region,
)


class TestDataSourceModel:
    """Tests for DataSource model."""

    def test_create_data_source(self, test_session: Session) -> None:
        """Test creating a data source with valid data."""
        data_source = DataSource(
            name="Test Source",
            type="csv",
            url="/path/to/file.csv",
            source_metadata={"version": "1.0"},
        )
        test_session.add(data_source)
        test_session.flush()

        assert data_source.id is not None
        assert data_source.name == "Test Source"
        assert data_source.type == "csv"
        assert data_source.url == "/path/to/file.csv"
        assert data_source.source_metadata == {"version": "1.0"}
        assert data_source.last_updated is not None

    def test_data_source_repr(self, sample_data_source: DataSource) -> None:
        """Test DataSource __repr__ method."""
        repr_str = repr(sample_data_source)
        assert "DataSource" in repr_str
        assert "Test Eurostat" in repr_str
        assert "api" in repr_str

    def test_data_source_required_fields(self, test_session: Session) -> None:
        """Test that required fields raise error when missing."""
        # name is required
        data_source = DataSource(type="csv", url="/path/to/file.csv")
        test_session.add(data_source)
        with pytest.raises(IntegrityError):
            test_session.flush()

    def test_data_source_relationships(
        self,
        test_session: Session,
        sample_demographic_data: list[DemographicData],
        sample_data_source: DataSource,
    ) -> None:
        """Test DataSource relationships with demographic data."""
        assert len(sample_data_source.demographic_data) == len(sample_demographic_data)


class TestRegionModel:
    """Tests for Region model."""

    def test_create_region(self, test_session: Session) -> None:
        """Test creating a region with valid data."""
        region = Region(
            code="DE",
            name="Germany",
            level="country",
        )
        test_session.add(region)
        test_session.flush()

        assert region.id is not None
        assert region.code == "DE"
        assert region.name == "Germany"
        assert region.level == "country"

    def test_region_repr(self, sample_region: Region) -> None:
        """Test Region __repr__ method."""
        repr_str = repr(sample_region)
        assert "Region" in repr_str
        assert "DE" in repr_str
        assert "Germany" in repr_str

    def test_region_unique_code(
        self, test_session: Session, sample_region: Region
    ) -> None:
        """Test that region code must be unique."""
        duplicate_region = Region(
            code="DE",  # Same code as sample_region
            name="Deutschland",
            level="country",
        )
        test_session.add(duplicate_region)
        with pytest.raises(IntegrityError):
            test_session.flush()

    def test_region_hierarchical_relationship(self, test_session: Session) -> None:
        """Test parent-child region relationship."""
        parent = Region(code="DE", name="Germany", level="country")
        test_session.add(parent)
        test_session.flush()

        child = Region(
            code="DE-BY",
            name="Bavaria",
            level="nuts1",
            parent_region_id=parent.id,
        )
        test_session.add(child)
        test_session.flush()

        assert child.parent_region == parent
        assert child in parent.sub_regions


class TestDemographicDataModel:
    """Tests for DemographicData model."""

    def test_create_demographic_data(
        self,
        test_session: Session,
        sample_region: Region,
        sample_data_source: DataSource,
    ) -> None:
        """Test creating demographic data with valid data."""
        demo_data = DemographicData(
            region_id=sample_region.id,
            data_source_id=sample_data_source.id,
            year=2023,
            age_min=0,
            age_max=5,
            gender="M",
            population=1000000,
        )
        test_session.add(demo_data)
        test_session.flush()

        assert demo_data.id is not None
        assert demo_data.year == 2023
        assert demo_data.age_min == 0
        assert demo_data.age_max == 5
        assert demo_data.gender == "M"
        assert demo_data.population == 1000000

    def test_demographic_data_repr(
        self, sample_demographic_data: list[DemographicData]
    ) -> None:
        """Test DemographicData __repr__ method."""
        repr_str = repr(sample_demographic_data[0])
        assert "DemographicData" in repr_str
        assert "2023" in repr_str

    def test_demographic_data_relationships(
        self,
        sample_demographic_data: list[DemographicData],
        sample_region: Region,
        sample_data_source: DataSource,
    ) -> None:
        """Test DemographicData relationships."""
        data = sample_demographic_data[0]
        assert data.region == sample_region
        assert data.data_source == sample_data_source

    def test_demographic_data_foreign_key_constraint(
        self, test_session: Session, sample_data_source: DataSource
    ) -> None:
        """Test that foreign key constraint is enforced."""
        demo_data = DemographicData(
            region_id=99999,  # Non-existent region
            data_source_id=sample_data_source.id,
            year=2023,
            gender="M",
            population=1000000,
        )
        test_session.add(demo_data)
        with pytest.raises(IntegrityError):
            test_session.flush()


class TestIndustrialDataModel:
    """Tests for IndustrialData model."""

    def test_create_industrial_data(
        self,
        test_session: Session,
        sample_region: Region,
        sample_data_source: DataSource,
    ) -> None:
        """Test creating industrial data with valid data."""
        industrial_data = IndustrialData(
            region_id=sample_region.id,
            data_source_id=sample_data_source.id,
            year=2023,
            month=12,
            nace_code="B-D",
            index_value=98,
            unit="I15",
        )
        test_session.add(industrial_data)
        test_session.flush()

        assert industrial_data.id is not None
        assert industrial_data.year == 2023
        assert industrial_data.month == 12
        assert industrial_data.nace_code == "B-D"
        assert industrial_data.index_value == 98
        assert industrial_data.unit == "I15"

    def test_industrial_data_repr(
        self, sample_industrial_data: list[IndustrialData]
    ) -> None:
        """Test IndustrialData __repr__ method."""
        repr_str = repr(sample_industrial_data[0])
        assert "IndustrialData" in repr_str
        assert "2023" in repr_str
        assert "B-D" in repr_str


class TestCapacityUtilizationModel:
    """Tests for CapacityUtilization model (GICPT)."""

    def test_create_capacity_utilization(
        self,
        test_session: Session,
        sample_region: Region,
        sample_data_source: DataSource,
    ) -> None:
        """Test creating capacity utilization data."""
        data = CapacityUtilization(
            region_id=sample_region.id,
            data_source_id=sample_data_source.id,
            year=2023,
            quarter=4,
            utilization_pct=82,
            sector="manufacturing",
        )
        test_session.add(data)
        test_session.flush()

        assert data.id is not None
        assert data.year == 2023
        assert data.quarter == 4
        assert data.utilization_pct == 82
        assert data.sector == "manufacturing"

    def test_capacity_utilization_repr(
        self, sample_capacity_utilization: CapacityUtilization
    ) -> None:
        """Test CapacityUtilization __repr__ method."""
        repr_str = repr(sample_capacity_utilization)
        assert "CapacityUtilization" in repr_str
        assert "2023" in repr_str
        assert "82" in repr_str

    def test_capacity_utilization_relationships(
        self,
        sample_capacity_utilization: CapacityUtilization,
        sample_region: Region,
        sample_data_source: DataSource,
    ) -> None:
        """Test CapacityUtilization relationships."""
        assert sample_capacity_utilization.region == sample_region
        assert sample_capacity_utilization.data_source == sample_data_source


class TestManufacturingOrdersModel:
    """Tests for ManufacturingOrders model (GICPT)."""

    def test_create_manufacturing_orders(
        self,
        test_session: Session,
        sample_region: Region,
        sample_data_source: DataSource,
    ) -> None:
        """Test creating manufacturing orders data."""
        data = ManufacturingOrders(
            region_id=sample_region.id,
            data_source_id=sample_data_source.id,
            year=2023,
            month=12,
            order_type="domestic",
            index_value=95,
            nace_code="C",
        )
        test_session.add(data)
        test_session.flush()

        assert data.id is not None
        assert data.order_type == "domestic"
        assert data.index_value == 95

    def test_manufacturing_orders_repr(
        self, sample_manufacturing_orders: list[ManufacturingOrders]
    ) -> None:
        """Test ManufacturingOrders __repr__ method."""
        repr_str = repr(sample_manufacturing_orders[0])
        assert "ManufacturingOrders" in repr_str
        assert "domestic" in repr_str


class TestEnergyConsumptionModel:
    """Tests for EnergyConsumption model (GICPT)."""

    def test_create_energy_consumption(
        self,
        test_session: Session,
        sample_region: Region,
        sample_data_source: DataSource,
    ) -> None:
        """Test creating energy consumption data."""
        data = EnergyConsumption(
            region_id=sample_region.id,
            data_source_id=sample_data_source.id,
            year=2023,
            month=12,
            energy_type="electricity",
            consumption_value=45000,
            unit="GWh",
            sector="industrial",
        )
        test_session.add(data)
        test_session.flush()

        assert data.id is not None
        assert data.energy_type == "electricity"
        assert data.consumption_value == 45000
        assert data.unit == "GWh"

    def test_energy_consumption_repr(
        self, sample_energy_consumption: list[EnergyConsumption]
    ) -> None:
        """Test EnergyConsumption __repr__ method."""
        repr_str = repr(sample_energy_consumption[0])
        assert "EnergyConsumption" in repr_str
        assert "electricity" in repr_str


class TestLaborMarketDataModel:
    """Tests for LaborMarketData model (GICPT)."""

    def test_create_labor_market_data(
        self,
        test_session: Session,
        sample_region: Region,
        sample_data_source: DataSource,
    ) -> None:
        """Test creating labor market data."""
        data = LaborMarketData(
            region_id=sample_region.id,
            data_source_id=sample_data_source.id,
            year=2023,
            month=12,
            metric_type="kurzarbeit",
            value=150000,
            unit="persons",
            sector="manufacturing",
        )
        test_session.add(data)
        test_session.flush()

        assert data.id is not None
        assert data.metric_type == "kurzarbeit"
        assert data.value == 150000

    def test_labor_market_data_repr(
        self, sample_labor_market_data: LaborMarketData
    ) -> None:
        """Test LaborMarketData __repr__ method."""
        repr_str = repr(sample_labor_market_data)
        assert "LaborMarketData" in repr_str
        assert "kurzarbeit" in repr_str


class TestComputedMetricModel:
    """Tests for ComputedMetric model (GICPT)."""

    def test_create_computed_metric(self, test_session: Session) -> None:
        """Test creating computed metric data."""
        data = ComputedMetric(
            metric_type="production_yoy",
            region_code="DE",
            period_type="monthly",
            period_year=2023,
            period_month=12,
            raw_value=97,
            yoy_change=-300,
            threshold_status="yellow",
            interpretation="Production down 3%",
        )
        test_session.add(data)
        test_session.flush()

        assert data.id is not None
        assert data.metric_type == "production_yoy"
        assert data.threshold_status == "yellow"

    def test_computed_metric_repr(self, sample_computed_metric: ComputedMetric) -> None:
        """Test ComputedMetric __repr__ method."""
        repr_str = repr(sample_computed_metric)
        assert "ComputedMetric" in repr_str
        assert "production_yoy" in repr_str
        assert "DE" in repr_str

    def test_computed_metric_quarterly(self, test_session: Session) -> None:
        """Test creating quarterly computed metric."""
        data = ComputedMetric(
            metric_type="capacity_utilization",
            region_code="DE",
            period_type="quarterly",
            period_year=2023,
            period_quarter=4,
            raw_value=82,
            threshold_status="green",
        )
        test_session.add(data)
        test_session.flush()

        assert data.period_month is None
        assert data.period_quarter == 4
