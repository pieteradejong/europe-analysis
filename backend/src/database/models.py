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
