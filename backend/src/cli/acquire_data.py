#!/usr/bin/env python3
"""
Command-line tool for data acquisition.

Usage:
    python -m backend.src.cli.acquire_data <source> <source_name> [--type csv|json|api] [--field-mapping key:value ...]
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# Add backend/src to path
backend_src = Path(__file__).parent.parent
sys.path.insert(0, str(backend_src))

from data_acquisition.pipeline import DataAcquisitionPipeline
from library import config, setup_logging

setup_logging(config)
logger = logging.getLogger(__name__)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Acquire demographic data from various sources"
    )
    parser.add_argument(
        "source",
        help="Source identifier (file path or URL)",
    )
    parser.add_argument(
        "source_name",
        help="Human-readable name for the source",
    )
    parser.add_argument(
        "--type",
        choices=["csv", "json", "api"],
        default=None,
        help="Source type (auto-detected if not provided)",
    )
    parser.add_argument(
        "--field-mapping",
        nargs="*",
        help="Field mappings in format key:value (e.g., age_group:age)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Parse field mappings
    field_mapping = None
    if args.field_mapping:
        field_mapping = {}
        for mapping in args.field_mapping:
            if ":" not in mapping:
                logger.error("Invalid field mapping format: %s (expected key:value)", mapping)
                sys.exit(1)
            key, value = mapping.split(":", 1)
            field_mapping[key.strip()] = value.strip()

    # Run pipeline
    pipeline = DataAcquisitionPipeline()
    try:
        logger.info("Starting data acquisition from: %s", args.source)
        result = pipeline.process(
            source=args.source,
            source_name=args.source_name,
            source_type=args.type,
            field_mapping=field_mapping,
        )

        if result.get("success"):
            print("\n✓ Data acquisition completed successfully!")
            print(f"  Source: {result['source']}")
            print(f"  Raw records: {result['raw_records']}")
            print(f"  Normalized records: {result['normalized_records']}")
            print(f"  Regions created: {result['regions_created']}")
            print(f"  Records inserted: {result['records_inserted']}")
            sys.exit(0)
        else:
            print(f"\n✗ Data acquisition failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)

    except Exception as e:
        logger.error("Error during data acquisition: %s", e, exc_info=True)
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

