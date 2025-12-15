"""
Database Module

This module provides database connection and session management using SQLAlchemy.
Supports both SQLite (development) and PostgreSQL/Supabase (production).
"""

from .base import Base, get_session, init_db
from .connection import create_engine, get_database_url

__all__ = ["Base", "get_session", "init_db", "create_engine", "get_database_url"]

