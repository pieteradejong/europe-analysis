#!/usr/bin/env python3
"""
Data inspection and validation tools.

Usage:
    python -m backend.src.cli.inspect_data sources
    python -m backend.src.cli.inspect_data regions [--query QUERY]
    python -m backend.src.cli.inspect_data demographics [--region-id ID] [--year YEAR]
    python -m backend.src.cli.inspect_data stats
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Add backend/src to path
backend_src = Path(__file__).parent.parent
sys.path.insert(0, str(backend_src))

from database import get_session
from database.repositories import (
    DataSourceRepository,
    DemographicRepository,
    RegionRepository,
)


def print_json(data: Any) -> None:
    """Print data as formatted JSON."""
    print(json.dumps(data, indent=2, default=str))


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Inspect and validate demographic data")
    subparsers = parser.add_subparsers(dest="command", help="Inspection command")

    # Sources command
    subparsers.add_parser("sources", help="List all data sources")

    # Regions command
    regions_parser = subparsers.add_parser("regions", help="List regions")
    regions_parser.add_argument(
        "--query",
        help="Search query to filter regions",
    )

    # Demographics command
    demo_parser = subparsers.add_parser("demographics", help="Query demographic data")
    demo_parser.add_argument("--region-id", type=int, help="Filter by region ID")
    demo_parser.add_argument("--region-code", help="Filter by region code")
    demo_parser.add_argument("--year", type=int, help="Filter by year")
    demo_parser.add_argument("--gender", help="Filter by gender (M/F/O/Total)")
    demo_parser.add_argument("--limit", type=int, default=100, help="Maximum results (default: 100)")

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Get database statistics")
    stats_parser.add_argument("--region-id", type=int, help="Filter by region ID")
    stats_parser.add_argument("--year", type=int, help="Filter by year")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    with get_session() as session:
        try:
            if args.command == "sources":
                repo = DataSourceRepository(session)
                sources = repo.list_all()
                print_json(
                    {
                        "count": len(sources),
                        "sources": [
                            {
                                "id": s.id,
                                "name": s.name,
                                "type": s.type,
                                "url": s.url,
                                "last_updated": s.last_updated.isoformat() if s.last_updated else None,
                            }
                            for s in sources
                        ],
                    }
                )

            elif args.command == "regions":
                repo = RegionRepository(session)
                if args.query:
                    regions = repo.search(args.query)
                else:
                    regions = repo.list_all()
                print_json(
                    {
                        "count": len(regions),
                        "regions": [
                            {
                                "id": r.id,
                                "code": r.code,
                                "name": r.name,
                                "level": r.level,
                            }
                            for r in regions
                        ],
                    }
                )

            elif args.command == "demographics":
                repo = DemographicRepository(session)
                data = repo.query(
                    region_id=args.region_id,
                    region_code=args.region_code,
                    year=args.year,
                    gender=args.gender,
                    limit=args.limit,
                )
                print_json(
                    {
                        "count": len(data),
                        "data": [
                            {
                                "id": d.id,
                                "region_code": d.region.code if d.region else None,
                                "region_name": d.region.name if d.region else None,
                                "year": d.year,
                                "age_min": d.age_min,
                                "age_max": d.age_max,
                                "gender": d.gender,
                                "population": d.population,
                            }
                            for d in data
                        ],
                    }
                )

            elif args.command == "stats":
                demo_repo = DemographicRepository(session)
                source_repo = DataSourceRepository(session)
                region_repo = RegionRepository(session)

                stats = demo_repo.get_statistics(region_id=args.region_id, year=args.year)

                print_json(
                    {
                        "total_sources": len(source_repo.list_all()),
                        "total_regions": len(region_repo.list_all()),
                        "demographics": stats,
                    }
                )

        except Exception as e:
            print(f"✗ Error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()

