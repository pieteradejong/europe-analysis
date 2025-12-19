"""
Database Base and Session Management

This module provides SQLAlchemy declarative base and session management.
"""

import logging
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .connection import create_engine

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""

    pass


# Create engine and session factory
_engine = create_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Get a database session (context manager).

    Yields:
        SQLAlchemy Session instance

    Example:
        with get_session() as session:
            # Use session
            pass
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """
    Initialize database by creating all tables.

    This should be called after all models are imported.
    """
    logger.info("Initializing database...")
    Base.metadata.create_all(bind=_engine)
    logger.info("Database initialized")


# Enable foreign key constraints for SQLite
@event.listens_for(_engine, "connect")
def set_sqlite_pragma(dbapi_conn: Any, connection_record: Any) -> None:
    """Enable foreign key constraints for SQLite."""
    if _engine.url.drivername == "sqlite":
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
