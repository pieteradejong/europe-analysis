"""
Database Module

This module provides database connection and session management using SQLAlchemy.
Supports both SQLite (development) and PostgreSQL/Supabase (production).
"""

from .base import Base, get_session, init_db
from .connection import create_engine, get_database_url

# Import models to ensure they're registered with Base.metadata
# This must happen before init_db() is called
from .models import DataSource, DemographicData, Region

__all__ = [
    "Base",
    "DataSource",
    "DemographicData",
    "Region",
    "create_engine",
    "get_database_url",
    "get_session",
    "init_db",
]
