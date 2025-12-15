"""
Data Acquisition Pipeline

This module orchestrates the data acquisition → normalization → storage flow.
"""

import logging
from typing import Any

from .base import AcquisitionResult
from .factory import DataAcquirerFactory
from .normalizer import DemographicNormalizer

from ..database import get_session
from ..database.repositories import (
    DataSourceRepository,
    DemographicRepository,
    RegionRepository,
)

logger = logging.getLogger(__name__)


class DataAcquisitionPipeline:
    """
    Pipeline for acquiring, normalizing, and storing demographic data.
    """

    def __init__(self) -> None:
        """Initialize the pipeline."""
        self.normalizer = DemographicNormalizer()

    def process(
        self,
        source: str,
        source_name: str,
        source_type: str | None = None,
        field_mapping: dict[str, str] | None = None,
        **acquirer_kwargs: Any,
    ) -> dict[str, Any]:
        """
        Process data from a source: acquire → normalize → store.

        Args:
            source: Source identifier (file path or URL)
            source_name: Human-readable name for the source
            source_type: Explicit source type (csv/json/api). If None, auto-detect
            field_mapping: Optional mapping from source fields to standard fields
            **acquirer_kwargs: Additional parameters for the acquirer

        Returns:
            Dictionary with processing results and statistics
        """
        logger.info("Starting data acquisition pipeline for: %s", source_name)

        # Step 1: Acquire data
        acquirer = DataAcquirerFactory.create(source, source_type, **acquirer_kwargs)
        acquisition_result = acquirer.acquire()

        if not acquisition_result.success:
            error_msg = f"Data acquisition failed: {acquisition_result.error}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "source": source_name,
            }

        if not acquisition_result.data:
            error_msg = "No data acquired from source"
            logger.warning(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "source": source_name,
            }

        logger.info(
            "Acquired %d raw records from %s", len(acquisition_result.data), source_name
        )

        # Step 2: Normalize data
        normalized_records = self.normalizer.normalize_batch(
            acquisition_result.data, field_mapping
        )

        if not normalized_records:
            error_msg = "No valid records after normalization"
            logger.warning(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "source": source_name,
                "raw_records": len(acquisition_result.data),
            }

        logger.info(
            "Normalized %d records into %d valid records",
            len(acquisition_result.data),
            len(normalized_records),
        )

        # Step 3: Store in database
        with get_session() as session:
            # Get or create data source
            source_repo = DataSourceRepository(session)
            data_source = source_repo.get_or_create(
                name=source_name,
                source_type=acquirer.__class__.__name__.replace("Acquirer", "").lower(),
                url=source,
                metadata=acquisition_result.metadata,
            )

            # Process records in batches
            region_repo = RegionRepository(session)
            demo_repo = DemographicRepository(session)

            stats = {
                "regions_created": 0,
                "records_inserted": 0,
                "regions": set(),
            }

            # Group records by region for efficient processing
            records_by_region: dict[str, list[dict[str, Any]]] = {}
            for record in normalized_records:
                region_code = record.get("region_code") or record.get("region_name")
                if region_code:
                    if region_code not in records_by_region:
                        records_by_region[region_code] = []
                    records_by_region[region_code].append(record)

            # Process each region
            for region_code, region_records in records_by_region.items():
                # Get or create region
                first_record = region_records[0]
                region = region_repo.get_or_create(
                    code=region_code,
                    name=first_record.get("region_name") or region_code,
                )

                if region_code not in stats["regions"]:
                    stats["regions"].add(region_code)
                    stats["regions_created"] += 1

                # Bulk insert demographic data
                count = demo_repo.bulk_insert(
                    region_records,
                    region_id=region.id,
                    data_source_id=data_source.id,
                )
                stats["records_inserted"] += count

            session.commit()

        logger.info(
            "Pipeline completed: %d regions, %d records inserted",
            stats["regions_created"],
            stats["records_inserted"],
        )

        return {
            "success": True,
            "source": source_name,
            "raw_records": len(acquisition_result.data),
            "normalized_records": len(normalized_records),
            "regions_created": stats["regions_created"],
            "records_inserted": stats["records_inserted"],
            "data_source_id": data_source.id,
        }

