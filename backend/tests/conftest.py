"""Shared test fixtures."""

import os
import tempfile
from collections.abc import Generator
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import (
    create_engine as sa_create_engine,
    event,
)
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.src.database.base import Base
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
from backend.src.library import AppConfig

# =============================================================================
# Configuration Fixtures
# =============================================================================


@pytest.fixture
def temp_env_file() -> Generator[Path, None, None]:
    """Create a temporary .env file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write(
            """
APP_ENV=testing
APP_DEBUG=true
APP_NAME=Test App
APP_VERSION=0.1.0
API_HOST=127.0.0.1
API_PORT=8000
LOG_LEVEL=DEBUG
        """.strip()
        )
    yield Path(f.name)
    os.unlink(f.name)


@pytest.fixture
def temp_json_config() -> Generator[Path, None, None]:
    """Create a temporary JSON config file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write('{"CANDIDATE_ID": "test-123"}')
    yield Path(f.name)
    os.unlink(f.name)


@pytest.fixture
def app_config(temp_env_file: Path) -> AppConfig:
    """Create an AppConfig instance for testing."""
    # In pydantic-settings v2, we need to use model_config or instantiate differently
    # Since env file support is built into AppConfig, we rely on environment variables
    return AppConfig()


# =============================================================================
# Database Fixtures
# =============================================================================


@pytest.fixture
def test_engine() -> Generator[Any, None, None]:
    """Create an in-memory SQLite engine for testing."""
    engine = sa_create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    # Enable foreign key constraints for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn: Any, connection_record: Any) -> None:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Create all tables
    Base.metadata.create_all(engine)

    yield engine

    # Cleanup
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def test_session(test_engine: Any) -> Generator[Session, None, None]:
    """Create a test database session."""
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = session_factory()
    try:
        yield session
        # Only commit if no pending rollback
        if session.is_active:
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        # Always rollback any pending changes before closing
        if session.is_active:
            session.rollback()
        session.close()


# =============================================================================
# Sample Data Fixtures
# =============================================================================


@pytest.fixture
def sample_data_source(test_session: Session) -> DataSource:
    """Create a sample data source for testing."""
    data_source = DataSource(
        name="Test Eurostat",
        type="api",
        url="https://ec.europa.eu/eurostat/api/test",
        source_metadata={"dataset_id": "demo_pjan"},
        last_updated=datetime.utcnow(),
    )
    test_session.add(data_source)
    test_session.flush()
    return data_source


@pytest.fixture
def sample_region(test_session: Session) -> Region:
    """Create a sample region (Germany) for testing."""
    region = Region(
        code="DE",
        name="Germany",
        level="country",
    )
    test_session.add(region)
    test_session.flush()
    return region


@pytest.fixture
def sample_region_france(test_session: Session) -> Region:
    """Create a sample region (France) for testing."""
    region = Region(
        code="FR",
        name="France",
        level="country",
    )
    test_session.add(region)
    test_session.flush()
    return region


@pytest.fixture
def sample_regions(test_session: Session) -> list[Region]:
    """Create multiple sample regions for testing."""
    regions = [
        Region(code="DE", name="Germany", level="country"),
        Region(code="FR", name="France", level="country"),
        Region(code="IT", name="Italy", level="country"),
        Region(code="ES", name="Spain", level="country"),
        Region(code="NL", name="Netherlands", level="country"),
    ]
    for region in regions:
        test_session.add(region)
    test_session.flush()
    return regions


@pytest.fixture
def sample_demographic_data(
    test_session: Session, sample_region: Region, sample_data_source: DataSource
) -> list[DemographicData]:
    """Create sample demographic data for testing."""
    data = [
        DemographicData(
            region_id=sample_region.id,
            data_source_id=sample_data_source.id,
            year=2023,
            age_min=0,
            age_max=5,
            gender="M",
            population=2000000,
        ),
        DemographicData(
            region_id=sample_region.id,
            data_source_id=sample_data_source.id,
            year=2023,
            age_min=0,
            age_max=5,
            gender="F",
            population=1900000,
        ),
        DemographicData(
            region_id=sample_region.id,
            data_source_id=sample_data_source.id,
            year=2023,
            age_min=5,
            age_max=10,
            gender="M",
            population=2100000,
        ),
        DemographicData(
            region_id=sample_region.id,
            data_source_id=sample_data_source.id,
            year=2022,
            age_min=0,
            age_max=5,
            gender="Total",
            population=3800000,
        ),
    ]
    for item in data:
        test_session.add(item)
    test_session.flush()
    return data


@pytest.fixture
def sample_industrial_data(
    test_session: Session, sample_region: Region, sample_data_source: DataSource
) -> list[IndustrialData]:
    """Create sample industrial data for testing."""
    data = [
        IndustrialData(
            region_id=sample_region.id,
            data_source_id=sample_data_source.id,
            year=2023,
            month=10,
            nace_code="B-D",
            index_value=98,
            unit="I15",
        ),
        IndustrialData(
            region_id=sample_region.id,
            data_source_id=sample_data_source.id,
            year=2023,
            month=11,
            nace_code="B-D",
            index_value=97,
            unit="I15",
        ),
        IndustrialData(
            region_id=sample_region.id,
            data_source_id=sample_data_source.id,
            year=2023,
            month=12,
            nace_code="C",
            index_value=95,
            unit="I15",
        ),
    ]
    for item in data:
        test_session.add(item)
    test_session.flush()
    return data


# =============================================================================
# GICPT Model Fixtures
# =============================================================================


@pytest.fixture
def sample_capacity_utilization(
    test_session: Session, sample_region: Region, sample_data_source: DataSource
) -> CapacityUtilization:
    """Create sample capacity utilization data for testing."""
    data = CapacityUtilization(
        region_id=sample_region.id,
        data_source_id=sample_data_source.id,
        year=2023,
        quarter=4,
        utilization_pct=82,
        sector="total",
    )
    test_session.add(data)
    test_session.flush()
    return data


@pytest.fixture
def sample_manufacturing_orders(
    test_session: Session, sample_region: Region, sample_data_source: DataSource
) -> list[ManufacturingOrders]:
    """Create sample manufacturing orders data for testing."""
    data = [
        ManufacturingOrders(
            region_id=sample_region.id,
            data_source_id=sample_data_source.id,
            year=2023,
            month=12,
            order_type="domestic",
            index_value=95,
            nace_code="C",
        ),
        ManufacturingOrders(
            region_id=sample_region.id,
            data_source_id=sample_data_source.id,
            year=2023,
            month=12,
            order_type="foreign",
            index_value=92,
            nace_code="C",
        ),
    ]
    for item in data:
        test_session.add(item)
    test_session.flush()
    return data


@pytest.fixture
def sample_energy_consumption(
    test_session: Session, sample_region: Region, sample_data_source: DataSource
) -> list[EnergyConsumption]:
    """Create sample energy consumption data for testing."""
    data = [
        EnergyConsumption(
            region_id=sample_region.id,
            data_source_id=sample_data_source.id,
            year=2023,
            month=12,
            energy_type="electricity",
            consumption_value=45000,
            unit="GWh",
            sector="industrial",
        ),
        EnergyConsumption(
            region_id=sample_region.id,
            data_source_id=sample_data_source.id,
            year=2023,
            month=12,
            energy_type="gas",
            consumption_value=38000,
            unit="TJ",
            sector="industrial",
        ),
    ]
    for item in data:
        test_session.add(item)
    test_session.flush()
    return data


@pytest.fixture
def sample_labor_market_data(
    test_session: Session, sample_region: Region, sample_data_source: DataSource
) -> LaborMarketData:
    """Create sample labor market data for testing."""
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
    return data


@pytest.fixture
def sample_computed_metric(test_session: Session) -> ComputedMetric:
    """Create sample computed metric for testing."""
    data = ComputedMetric(
        metric_type="production_yoy",
        region_code="DE",
        period_type="monthly",
        period_year=2023,
        period_month=12,
        period_quarter=None,
        raw_value=97,
        yoy_change=-300,  # -3.0%
        threshold_status="yellow",
        interpretation="Production down 3% YoY, indicating slowdown",
    )
    test_session.add(data)
    test_session.flush()
    return data


# =============================================================================
# Mock Eurostat Response Fixtures
# =============================================================================


@pytest.fixture
def mock_eurostat_jsonstat_response() -> dict[str, Any]:
    """Create a mock Eurostat JSON-stat 2.0 response."""
    return {
        "version": "2.0",
        "class": "dataset",
        "label": "Population on 1 January by age and sex",
        "id": ["geo", "time", "sex", "age"],
        "size": [2, 2, 2, 3],
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
            "sex": {
                "category": {
                    "index": {"M": 0, "F": 1},
                    "label": {"M": "Males", "F": "Females"},
                }
            },
            "age": {
                "category": {
                    "index": {"Y0-4": 0, "Y5-9": 1, "Y_GE85": 2},
                    "label": {
                        "Y0-4": "From 0 to 4 years",
                        "Y5-9": "From 5 to 9 years",
                        "Y_GE85": "85 years or over",
                    },
                }
            },
        },
        "value": [
            # DE, 2022, M: Y0-4, Y5-9, Y_GE85
            2000000,
            2100000,
            500000,
            # DE, 2022, F: Y0-4, Y5-9, Y_GE85
            1900000,
            2000000,
            800000,
            # DE, 2023, M: Y0-4, Y5-9, Y_GE85
            1980000,
            2080000,
            520000,
            # DE, 2023, F: Y0-4, Y5-9, Y_GE85
            1880000,
            1980000,
            820000,
            # FR, 2022, M: Y0-4, Y5-9, Y_GE85
            1800000,
            1900000,
            450000,
            # FR, 2022, F: Y0-4, Y5-9, Y_GE85
            1700000,
            1800000,
            700000,
            # FR, 2023, M: Y0-4, Y5-9, Y_GE85
            1780000,
            1880000,
            470000,
            # FR, 2023, F: Y0-4, Y5-9, Y_GE85
            1680000,
            1780000,
            720000,
        ],
    }


@pytest.fixture
def mock_eurostat_sparse_response() -> dict[str, Any]:
    """Create a mock Eurostat JSON-stat response with sparse values."""
    return {
        "version": "2.0",
        "class": "dataset",
        "id": ["geo", "time"],
        "size": [2, 3],
        "dimension": {
            "geo": {
                "category": {
                    "index": ["DE", "FR"],
                    "label": {"DE": "Germany", "FR": "France"},
                }
            },
            "time": {
                "category": {
                    "index": ["2021", "2022", "2023"],
                    "label": {"2021": "2021", "2022": "2022", "2023": "2023"},
                }
            },
        },
        # Sparse format: index -> value (some missing)
        "value": {
            "0": 83000000,  # DE, 2021
            "2": 83500000,  # DE, 2023
            "3": 67000000,  # FR, 2021
            "4": 67200000,  # FR, 2022
            "5": 67400000,  # FR, 2023
        },
    }


@pytest.fixture
def mock_eurostat_industrial_response() -> dict[str, Any]:
    """Create a mock Eurostat JSON-stat response for industrial data."""
    return {
        "version": "2.0",
        "class": "dataset",
        "id": ["geo", "time", "nace_r2", "unit", "s_adj"],
        "size": [1, 3, 1, 1, 1],
        "dimension": {
            "geo": {
                "category": {
                    "index": {"DE": 0},
                    "label": {"DE": "Germany"},
                }
            },
            "time": {
                "category": {
                    "index": {"2023M10": 0, "2023M11": 1, "2023M12": 2},
                    "label": {
                        "2023M10": "October 2023",
                        "2023M11": "November 2023",
                        "2023M12": "December 2023",
                    },
                }
            },
            "nace_r2": {
                "category": {
                    "index": {"B-D": 0},
                    "label": {"B-D": "Industry (except construction)"},
                }
            },
            "unit": {
                "category": {
                    "index": {"I15": 0},
                    "label": {"I15": "Index, 2015=100"},
                }
            },
            "s_adj": {
                "category": {
                    "index": {"SCA": 0},
                    "label": {"SCA": "Seasonally and calendar adjusted"},
                }
            },
        },
        "value": [98.5, 97.2, 96.8],
    }
