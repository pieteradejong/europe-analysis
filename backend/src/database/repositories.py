"""
Database Repositories

This module provides repository classes for database operations,
following the repository pattern for clean separation of concerns.
"""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from .models import DataSource, DemographicData, IndustrialData, Region

logger = logging.getLogger(__name__)


class DataSourceRepository:
    """Repository for DataSource operations."""

    def __init__(self, session: Session) -> None:
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    def get_or_create(
        self,
        name: str,
        source_type: str,
        url: str,
        metadata: dict[str, Any] | None = None,
    ) -> DataSource:
        """
        Get existing data source or create new one.

        Args:
            name: Source name
            source_type: Type of source (csv/json/api)
            url: Source URL or file path
            metadata: Optional metadata dictionary

        Returns:
            DataSource instance
        """
        data_source = (
            self.session.query(DataSource)
            .filter(DataSource.name == name, DataSource.url == url)
            .first()
        )

        if data_source:
            # Update last_updated timestamp
            data_source.last_updated = datetime.utcnow()  # type: ignore[assignment]
            if metadata:
                data_source.source_metadata = metadata  # type: ignore[assignment]
            return data_source

        data_source = DataSource(
            name=name,
            type=source_type,
            url=url,
            source_metadata=metadata or {},
            last_updated=datetime.utcnow(),
        )
        self.session.add(data_source)
        self.session.flush()
        logger.info("Created new data source: %s (%s)", name, source_type)
        return data_source

    def get_by_id(self, source_id: int) -> DataSource | None:
        """Get data source by ID."""
        return self.session.query(DataSource).filter(DataSource.id == source_id).first()

    def list_all(self) -> list[DataSource]:
        """List all data sources."""
        return self.session.query(DataSource).all()


class RegionRepository:
    """Repository for Region operations."""

    def __init__(self, session: Session) -> None:
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    def get_or_create(
        self,
        code: str,
        name: str,
        level: str | None = None,
        parent_region_id: int | None = None,
    ) -> Region:
        """
        Get existing region or create new one.

        Args:
            code: Region code (ISO code or identifier)
            name: Region name
            level: Region level (country/nuts1/nuts2/nuts3/city)
            parent_region_id: Optional parent region ID

        Returns:
            Region instance
        """
        region = self.session.query(Region).filter(Region.code == code).first()

        if region:
            # Update name if changed
            if region.name != name:
                region.name = name  # type: ignore[assignment]
            if level and region.level != level:
                region.level = level  # type: ignore[assignment]
            if parent_region_id and region.parent_region_id != parent_region_id:
                region.parent_region_id = parent_region_id  # type: ignore[assignment]
            return region

        region = Region(
            code=code,
            name=name,
            level=level,
            parent_region_id=parent_region_id,
        )
        self.session.add(region)
        self.session.flush()
        logger.info("Created new region: %s (%s)", code, name)
        return region

    def get_by_code(self, code: str) -> Region | None:
        """Get region by code."""
        return self.session.query(Region).filter(Region.code == code).first()

    def get_by_id(self, region_id: int) -> Region | None:
        """Get region by ID."""
        return self.session.query(Region).filter(Region.id == region_id).first()

    def list_all(self) -> list[Region]:
        """List all regions."""
        return self.session.query(Region).all()

    def search(self, query: str) -> list[Region]:
        """
        Search regions by code or name.

        Args:
            query: Search query string

        Returns:
            List of matching regions
        """
        return (
            self.session.query(Region)
            .filter(
                or_(
                    Region.code.ilike(f"%{query}%"),
                    Region.name.ilike(f"%{query}%"),
                )
            )
            .all()
        )


class DemographicRepository:
    """Repository for DemographicData operations."""

    def __init__(self, session: Session) -> None:
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    def bulk_insert(
        self,
        records: list[dict[str, Any]],
        region_id: int,
        data_source_id: int,
    ) -> int:
        """
        Bulk insert demographic records.

        Args:
            records: List of normalized demographic records
            region_id: Region ID
            data_source_id: Data source ID

        Returns:
            Number of records inserted
        """
        demographic_objects = []
        for record in records:
            demographic = DemographicData(
                region_id=region_id,
                data_source_id=data_source_id,
                year=record.get("year"),
                age_min=record.get("age_min"),
                age_max=record.get("age_max"),
                gender=record.get("gender", "Total"),
                population=record.get("population", 0),
            )
            demographic_objects.append(demographic)

        self.session.bulk_save_objects(demographic_objects)
        self.session.flush()
        count = len(demographic_objects)
        logger.info("Bulk inserted %d demographic records", count)
        return count

    def query(
        self,
        region_id: int | None = None,
        region_code: str | None = None,
        year: int | None = None,
        gender: str | None = None,
        age_min: int | None = None,
        age_max: int | None = None,
        limit: int | None = None,
    ) -> list[DemographicData]:
        """
        Query demographic data with filters.

        Args:
            region_id: Filter by region ID
            region_code: Filter by region code
            year: Filter by year
            gender: Filter by gender (M/F/O/Total)
            age_min: Filter by minimum age
            age_max: Filter by maximum age
            limit: Maximum number of results

        Returns:
            List of DemographicData instances
        """
        query = self.session.query(DemographicData)

        if region_id:
            query = query.filter(DemographicData.region_id == region_id)
        elif region_code:
            query = query.join(Region).filter(Region.code == region_code)

        if year:
            query = query.filter(DemographicData.year == year)

        if gender:
            query = query.filter(DemographicData.gender == gender)

        if age_min is not None:
            query = query.filter(
                or_(
                    DemographicData.age_min == age_min,
                    and_(
                        DemographicData.age_min <= age_min,
                        or_(
                            DemographicData.age_max > age_min,
                            DemographicData.age_max.is_(None),
                        ),
                    ),
                )
            )

        if age_max is not None:
            query = query.filter(
                or_(
                    DemographicData.age_max == age_max,
                    DemographicData.age_max.is_(None),
                    DemographicData.age_max > age_max,
                )
            )

        if limit:
            query = query.limit(limit)

        return query.all()

    def get_statistics(
        self,
        region_id: int | None = None,
        year: int | None = None,
    ) -> dict[str, Any]:
        """
        Get demographic statistics.

        Args:
            region_id: Optional region ID to filter
            year: Optional year to filter

        Returns:
            Dictionary with statistics
        """
        query = self.session.query(DemographicData)

        if region_id:
            query = query.filter(DemographicData.region_id == region_id)
        if year:
            query = query.filter(DemographicData.year == year)

        total_records = query.count()

        # Get year range
        min_year = query.with_entities(func.min(DemographicData.year)).scalar()
        max_year = query.with_entities(func.max(DemographicData.year)).scalar()

        years_covered = f"{min_year}-{max_year}" if min_year and max_year else "N/A"

        return {
            "total_records": total_records,
            "years_covered": years_covered,
        }

    def delete_by_source(self, data_source_id: int) -> int:
        """
        Delete all demographic data from a specific source.

        Args:
            data_source_id: Data source ID

        Returns:
            Number of records deleted
        """
        count = (
            self.session.query(DemographicData)
            .filter(DemographicData.data_source_id == data_source_id)
            .delete()
        )
        self.session.flush()
        logger.info("Deleted %d records for data source %d", count, data_source_id)
        return count


class IndustrialRepository:
    """Repository for IndustrialData operations."""

    def __init__(self, session: Session) -> None:
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    def bulk_insert(
        self,
        records: list[dict[str, Any]],
        region_id: int,
        data_source_id: int,
    ) -> int:
        """
        Bulk insert industrial records.

        Args:
            records: List of normalized industrial records
            region_id: Region ID
            data_source_id: Data source ID

        Returns:
            Number of records inserted
        """
        industrial_objects = []
        for record in records:
            industrial = IndustrialData(
                region_id=region_id,
                data_source_id=data_source_id,
                year=record.get("year"),
                month=record.get("month"),
                nace_code=record.get("nace_code"),
                index_value=record.get("index_value"),
                unit=record.get("unit"),
            )
            industrial_objects.append(industrial)

        self.session.bulk_save_objects(industrial_objects)
        self.session.flush()
        count = len(industrial_objects)
        logger.info("Bulk inserted %d industrial records", count)
        return count

    def query(
        self,
        region_id: int | None = None,
        region_code: str | None = None,
        year: int | None = None,
        month: int | None = None,
        nace_code: str | None = None,
        limit: int | None = None,
    ) -> list[IndustrialData]:
        """
        Query industrial data with filters.

        Args:
            region_id: Filter by region ID
            region_code: Filter by region code
            year: Filter by year
            month: Filter by month (1-12)
            nace_code: Filter by NACE industry code
            limit: Maximum number of results

        Returns:
            List of IndustrialData instances
        """
        query = self.session.query(IndustrialData)

        if region_id:
            query = query.filter(IndustrialData.region_id == region_id)
        elif region_code:
            query = query.join(Region).filter(Region.code == region_code)

        if year:
            query = query.filter(IndustrialData.year == year)

        if month:
            query = query.filter(IndustrialData.month == month)

        if nace_code:
            query = query.filter(IndustrialData.nace_code == nace_code)

        # Order by year and month descending for latest first
        query = query.order_by(
            IndustrialData.year.desc(),
            IndustrialData.month.desc(),
        )

        if limit:
            query = query.limit(limit)

        return query.all()

    def get_statistics(
        self,
        region_id: int | None = None,
        year: int | None = None,
    ) -> dict[str, Any]:
        """
        Get industrial data statistics.

        Args:
            region_id: Optional region ID to filter
            year: Optional year to filter

        Returns:
            Dictionary with statistics
        """
        query = self.session.query(IndustrialData)

        if region_id:
            query = query.filter(IndustrialData.region_id == region_id)
        if year:
            query = query.filter(IndustrialData.year == year)

        total_records = query.count()

        # Get year range
        min_year = query.with_entities(func.min(IndustrialData.year)).scalar()
        max_year = query.with_entities(func.max(IndustrialData.year)).scalar()

        years_covered = f"{min_year}-{max_year}" if min_year and max_year else "N/A"

        # Get unique NACE codes
        nace_codes = query.with_entities(IndustrialData.nace_code).distinct().all()
        nace_codes = [code[0] for code in nace_codes if code[0]]

        return {
            "total_records": total_records,
            "years_covered": years_covered,
            "nace_codes": nace_codes,
        }

    def delete_by_source(self, data_source_id: int) -> int:
        """
        Delete all industrial data from a specific source.

        Args:
            data_source_id: Data source ID

        Returns:
            Number of records deleted
        """
        count = (
            self.session.query(IndustrialData)
            .filter(IndustrialData.data_source_id == data_source_id)
            .delete()
        )
        self.session.flush()
        logger.info(
            "Deleted %d industrial records for data source %d", count, data_source_id
        )
        return count
