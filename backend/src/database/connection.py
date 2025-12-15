"""
Database Connection Factory

This module provides database connection management with support for
both SQLite and PostgreSQL/Supabase.
"""

import logging
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine as sa_create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from ..library import config

logger = logging.getLogger(__name__)


def get_database_url() -> str:
    """
    Get database URL from configuration.

    Returns:
        Database connection URL string
    """
    database_url = config.DATABASE_URL

    # Ensure SQLite database directory exists
    if database_url.startswith("sqlite"):
        # Extract path from sqlite:///path/to/db.db
        db_path = database_url.replace("sqlite:///", "")
        db_file = Path(db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        logger.debug("SQLite database path: %s", db_file)

    return database_url


def create_engine(**kwargs: Any) -> Engine:
    """
    Create SQLAlchemy engine with appropriate configuration.

    Args:
        **kwargs: Additional engine configuration options

    Returns:
        SQLAlchemy Engine instance
    """
    database_url = get_database_url()

    # SQLite-specific configuration
    if database_url.startswith("sqlite"):
        engine_kwargs: dict[str, Any] = {
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
            "echo": config.DEBUG,  # Log SQL queries in debug mode
        }
        engine_kwargs.update(kwargs)
        engine = sa_create_engine(database_url, **engine_kwargs)
        logger.info("Created SQLite engine: %s", database_url)
        return engine

    # PostgreSQL/Supabase configuration
    engine_kwargs = {
        "pool_pre_ping": True,  # Verify connections before using
        "pool_size": 5,
        "max_overflow": 10,
        "echo": config.DEBUG,
    }
    engine_kwargs.update(kwargs)
    engine = sa_create_engine(database_url, **engine_kwargs)
    logger.info("Created PostgreSQL engine")
    return engine

