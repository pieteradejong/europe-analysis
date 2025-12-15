#!/usr/bin/env python3
"""
Database migration helper.

Usage:
    python -m backend.src.cli.migrate_db upgrade [revision]
    python -m backend.src.cli.migrate_db downgrade [revision]
    python -m backend.src.cli.migrate_db current
    python -m backend.src.cli.migrate_db history
"""

import argparse
import sys
from pathlib import Path

# Add backend/src to path
backend_src = Path(__file__).parent.parent
sys.path.insert(0, str(backend_src))

try:
    from alembic import command
    from alembic.config import Config
except ImportError:
    print("Error: Alembic is not installed. Run: pip install alembic")
    sys.exit(1)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Database migration helper")
    subparsers = parser.add_subparsers(dest="command", help="Migration command")

    # Upgrade command
    upgrade_parser = subparsers.add_parser("upgrade", help="Upgrade database to a revision")
    upgrade_parser.add_argument(
        "revision",
        nargs="?",
        default="head",
        help="Target revision (default: head)",
    )

    # Downgrade command
    downgrade_parser = subparsers.add_parser("downgrade", help="Downgrade database to a revision")
    downgrade_parser.add_argument(
        "revision",
        nargs="?",
        default="-1",
        help="Target revision (default: -1)",
    )

    # Current command
    subparsers.add_parser("current", help="Show current database revision")

    # History command
    subparsers.add_parser("history", help="Show migration history")

    # Create tables command (for initial setup)
    subparsers.add_parser("create-tables", help="Create all tables (for initial setup)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Get alembic config
    alembic_cfg = Config(str(Path(__file__).parent.parent.parent / "backend" / "alembic.ini"))

    try:
        if args.command == "upgrade":
            print(f"Upgrading database to revision: {args.revision}")
            command.upgrade(alembic_cfg, args.revision)
            print("✓ Database upgraded successfully")

        elif args.command == "downgrade":
            print(f"Downgrading database to revision: {args.revision}")
            command.downgrade(alembic_cfg, args.revision)
            print("✓ Database downgraded successfully")

        elif args.command == "current":
            command.current(alembic_cfg)

        elif args.command == "history":
            command.history(alembic_cfg)

        elif args.command == "create-tables":
            print("Creating database tables...")
            from database import init_db

            init_db()
            print("✓ Database tables created successfully")

    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

