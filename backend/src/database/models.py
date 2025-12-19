"""
Database Models

This module defines SQLAlchemy models for demographic data storage.
"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from .base import Base


class DataSource(Base):
    """Model representing a data source (CSV, JSON, or API)."""

    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    type = Column(String, nullable=False)  # csv, json, api
    url = Column(String, nullable=False)  # file path or API endpoint
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    source_metadata = Column(JSON, default=dict)  # Source-specific metadata

    # Relationships
    demographic_data = relationship("DemographicData", back_populates="data_source")
    industrial_data = relationship("IndustrialData", back_populates="data_source")
    capacity_utilization = relationship(
        "CapacityUtilization", back_populates="data_source"
    )
    manufacturing_orders = relationship(
        "ManufacturingOrders", back_populates="data_source"
    )
    energy_consumption = relationship("EnergyConsumption", back_populates="data_source")
    labor_market_data = relationship("LaborMarketData", back_populates="data_source")

    def __repr__(self) -> str:
        return f"<DataSource(id={self.id}, name='{self.name}', type='{self.type}')>"


class Region(Base):
    """Model representing a geographic region."""

    __tablename__ = "regions"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(
        String, unique=True, nullable=False, index=True
    )  # ISO code or identifier
    name = Column(String, nullable=False)
    parent_region_id = Column(Integer, ForeignKey("regions.id"), nullable=True)
    level = Column(String, nullable=True)  # country, nuts1, nuts2, nuts3, city

    # Self-referential relationship for hierarchical regions
    parent_region = relationship("Region", remote_side=[id], backref="sub_regions")

    # Relationships
    demographic_data = relationship("DemographicData", back_populates="region")
    industrial_data = relationship("IndustrialData", back_populates="region")
    capacity_utilization = relationship("CapacityUtilization", back_populates="region")
    manufacturing_orders = relationship("ManufacturingOrders", back_populates="region")
    energy_consumption = relationship("EnergyConsumption", back_populates="region")
    labor_market_data = relationship("LaborMarketData", back_populates="region")

    def __repr__(self) -> str:
        return f"<Region(id={self.id}, code='{self.code}', name='{self.name}')>"


class DemographicData(Base):
    """Model representing demographic data for a region."""

    __tablename__ = "demographic_data"

    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False, index=True)
    data_source_id = Column(
        Integer, ForeignKey("data_sources.id"), nullable=False, index=True
    )
    year = Column(Integer, nullable=True, index=True)
    age_min = Column(Integer, nullable=True)  # Minimum age (inclusive)
    age_max = Column(
        Integer, nullable=True
    )  # Maximum age (exclusive, None for open-ended)
    gender = Column(String, nullable=False)  # M, F, O, Total
    population = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    region = relationship("Region", back_populates="demographic_data")
    data_source = relationship("DataSource", back_populates="demographic_data")

    # Composite index for fast queries
    __table_args__ = (
        Index(
            "idx_region_year_age_gender",
            "region_id",
            "year",
            "age_min",
            "gender",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<DemographicData(id={self.id}, region_id={self.region_id}, "
            f"year={self.year}, age={self.age_min}-{self.age_max}, "
            f"gender={self.gender}, population={self.population})>"
        )


class IndustrialData(Base):
    """Model representing industrial production data for a region."""

    __tablename__ = "industrial_data"

    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False, index=True)
    data_source_id = Column(
        Integer, ForeignKey("data_sources.id"), nullable=False, index=True
    )
    year = Column(Integer, nullable=True, index=True)
    month = Column(Integer, nullable=True)  # 1-12 for monthly data
    nace_code = Column(
        String, nullable=True
    )  # Industry classification (e.g., "B-D", "C")
    index_value = Column(
        Integer, nullable=True
    )  # Industrial production index (2015=100)
    unit = Column(String, nullable=True)  # e.g., "I15" (index 2015=100)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    region = relationship("Region", back_populates="industrial_data")
    data_source = relationship("DataSource", back_populates="industrial_data")

    # Composite index for fast queries
    __table_args__ = (
        Index(
            "idx_industrial_region_year_month",
            "region_id",
            "year",
            "month",
            "nace_code",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<IndustrialData(id={self.id}, region_id={self.region_id}, "
            f"year={self.year}, month={self.month}, nace_code={self.nace_code}, "
            f"index_value={self.index_value})>"
        )


# =============================================================================
# GICPT (German Industrial Capacity & Production Tracker) Models
# =============================================================================


class CapacityUtilization(Base):
    """Model representing manufacturing capacity utilization (quarterly)."""

    __tablename__ = "capacity_utilization"

    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False, index=True)
    data_source_id = Column(
        Integer, ForeignKey("data_sources.id"), nullable=False, index=True
    )
    year = Column(Integer, nullable=False, index=True)
    quarter = Column(Integer, nullable=False)  # 1-4
    utilization_pct = Column(Integer, nullable=True)  # 0-100
    sector = Column(String, nullable=True)  # NACE code or "total"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    region = relationship("Region", back_populates="capacity_utilization")
    data_source = relationship("DataSource", back_populates="capacity_utilization")

    # Composite index for fast queries
    __table_args__ = (
        Index(
            "idx_capacity_region_year_quarter",
            "region_id",
            "year",
            "quarter",
            "sector",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<CapacityUtilization(id={self.id}, region_id={self.region_id}, "
            f"year={self.year}, quarter={self.quarter}, "
            f"utilization_pct={self.utilization_pct})>"
        )


class ManufacturingOrders(Base):
    """Model representing new manufacturing orders (monthly)."""

    __tablename__ = "manufacturing_orders"

    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False, index=True)
    data_source_id = Column(
        Integer, ForeignKey("data_sources.id"), nullable=False, index=True
    )
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False)  # 1-12
    order_type = Column(String, nullable=False)  # "domestic", "foreign", "total"
    index_value = Column(Integer, nullable=True)  # Index value (2015=100)
    nace_code = Column(String, nullable=True)  # Industry classification
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    region = relationship("Region", back_populates="manufacturing_orders")
    data_source = relationship("DataSource", back_populates="manufacturing_orders")

    # Composite index for fast queries
    __table_args__ = (
        Index(
            "idx_orders_region_year_month",
            "region_id",
            "year",
            "month",
            "order_type",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<ManufacturingOrders(id={self.id}, region_id={self.region_id}, "
            f"year={self.year}, month={self.month}, order_type={self.order_type}, "
            f"index_value={self.index_value})>"
        )


class EnergyConsumption(Base):
    """Model representing industrial energy consumption (monthly)."""

    __tablename__ = "energy_consumption"

    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False, index=True)
    data_source_id = Column(
        Integer, ForeignKey("data_sources.id"), nullable=False, index=True
    )
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=True)  # 1-12, None for annual
    energy_type = Column(String, nullable=False)  # "electricity", "gas"
    consumption_value = Column(Integer, nullable=True)  # Consumption value
    unit = Column(String, nullable=True)  # "TJ", "GWh", etc.
    sector = Column(String, nullable=True)  # "industrial", "total"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    region = relationship("Region", back_populates="energy_consumption")
    data_source = relationship("DataSource", back_populates="energy_consumption")

    # Composite index for fast queries
    __table_args__ = (
        Index(
            "idx_energy_region_year_month",
            "region_id",
            "year",
            "month",
            "energy_type",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<EnergyConsumption(id={self.id}, region_id={self.region_id}, "
            f"year={self.year}, month={self.month}, energy_type={self.energy_type}, "
            f"consumption_value={self.consumption_value})>"
        )


class LaborMarketData(Base):
    """Model representing labor market data (Kurzarbeit, hours worked)."""

    __tablename__ = "labor_market_data"

    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False, index=True)
    data_source_id = Column(
        Integer, ForeignKey("data_sources.id"), nullable=False, index=True
    )
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=True)  # 1-12, None for annual
    metric_type = Column(String, nullable=False)  # "kurzarbeit", "hours_worked"
    value = Column(Integer, nullable=True)  # Count or hours
    unit = Column(String, nullable=True)  # "persons", "hours", etc.
    sector = Column(String, nullable=True)  # Industry sector if applicable
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    region = relationship("Region", back_populates="labor_market_data")
    data_source = relationship("DataSource", back_populates="labor_market_data")

    # Composite index for fast queries
    __table_args__ = (
        Index(
            "idx_labor_region_year_month",
            "region_id",
            "year",
            "month",
            "metric_type",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<LaborMarketData(id={self.id}, region_id={self.region_id}, "
            f"year={self.year}, month={self.month}, metric_type={self.metric_type}, "
            f"value={self.value})>"
        )


class ComputedMetric(Base):
    """Model for pre-computed analytics (YoY, thresholds, signals)."""

    __tablename__ = "computed_metrics"

    id = Column(Integer, primary_key=True, index=True)
    metric_type = Column(
        String, nullable=False, index=True
    )  # "production_yoy", "capacity_signal", etc.
    region_code = Column(String, nullable=False, index=True)
    period_type = Column(String, nullable=False)  # "monthly", "quarterly"
    period_year = Column(Integer, nullable=False)
    period_month = Column(
        Integer, nullable=True
    )  # 1-12 for monthly, None for quarterly
    period_quarter = Column(Integer, nullable=True)  # 1-4 for quarterly
    raw_value = Column(Integer, nullable=True)
    yoy_change = Column(Integer, nullable=True)  # YoY % change * 100 (for precision)
    threshold_status = Column(String, nullable=True)  # "green", "yellow", "red"
    interpretation = Column(String, nullable=True)  # Text explanation
    computed_at = Column(DateTime, default=datetime.utcnow)

    # Composite index for fast queries
    __table_args__ = (
        Index(
            "idx_computed_type_region_period",
            "metric_type",
            "region_code",
            "period_year",
            "period_month",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<ComputedMetric(id={self.id}, metric_type={self.metric_type}, "
            f"region_code={self.region_code}, period={self.period_year}/{self.period_month})>"
        )
