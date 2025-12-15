"""
Base App - Main Application Entry Point

This module initializes and runs the application with proper configuration
and logging setup.
"""

import logging
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .library import config, setup_logging


def init_app(config_path: Path | None = None) -> None:
    """
    Initialize the application with configuration and logging.

    Args:
        config_path: Optional path to JSON config file
    """
    # Setup logging first so we can log the initialization process
    setup_logging(config)
    logger = logging.getLogger(__name__)

    try:
        # Load JSON config if provided
        if config_path:
            from .library import load_json_config

            load_json_config(str(config_path))
            logger.info("Loaded JSON configuration from %s", config_path)

        logger.info("Initializing %s v%s", config.APP_NAME, config.APP_VERSION)
        logger.info("Environment: %s (Debug: %s)", config.ENV, config.DEBUG)
        logger.info("API will run on %s:%d", config.API_HOST, config.API_PORT)

    except Exception as e:
        logger.error("Failed to initialize application: %s", e, exc_info=True)
        raise


def main() -> None:
    """Run the application."""
    logger = logging.getLogger(__name__)
    try:
        logger.info("Starting application...")
        # Application startup code here

    except Exception as e:
        logger.error("Application failed: %s", e, exc_info=True)
        raise
    finally:
        logger.info("Application shutdown complete")


class APIError(BaseModel):
    """API error response model."""

    detail: str
    code: str | None = None
    extra: Any | None = None


# Create FastAPI app with proper metadata
app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    description="A modern, type-safe Python web application template",
    docs_url="/docs" if config.DEBUG else None,  # Disable docs in production
    redoc_url="/redoc" if config.DEBUG else None,
)

# Security middleware - only restrict hosts in production
# Note: TrustedHostMiddleware can be restrictive in development, enable in production
# if not config.DEBUG:
#     app.add_middleware(
#         TrustedHostMiddleware,
#         allowed_hosts=["yourdomain.com"]
#     )

# CORS middleware - configure for your needs
app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        ["http://localhost:5173", "http://localhost:3000"]
        if config.DEBUG
        else ["https://yourdomain.com"]
    ),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    if not config.DEBUG:
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )

    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=APIError(detail=exc.detail, code=str(exc.status_code)).dict(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Handle unhandled exceptions."""
    # Log the full exception for debugging
    logger = logging.getLogger(__name__)
    logger.error("Unhandled exception: %s", exc, exc_info=True)

    # Return generic error in production, detailed in development
    detail = str(exc) if config.DEBUG else "Internal server error"
    return JSONResponse(
        status_code=500,
        content=APIError(detail=detail, code="internal_error").dict(),
    )


@app.get("/")
async def root():
    """Root endpoint with basic app info."""
    return {
        "name": config.APP_NAME,
        "version": config.APP_VERSION,
        "environment": config.ENV,
        "status": "healthy",
    }


@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "backend"}


@app.get("/health/model")
async def model_health_check():
    """Model health check endpoint."""
    return {"status": "healthy", "service": "model"}


@app.get("/notfound")
async def not_found_example():
    """Example endpoint that raises a 404 error."""
    raise HTTPException(status_code=404, detail="Item not found")


# Data Acquisition and Querying Endpoints

from pydantic import Field

from .data_acquisition.pipeline import DataAcquisitionPipeline
from .database import get_session
from .database.repositories import (
    DataSourceRepository,
    DemographicRepository,
    RegionRepository,
)


class AcquireDataRequest(BaseModel):
    """Request model for data acquisition."""

    source: str = Field(description="Source identifier (file path or URL)")
    source_name: str = Field(description="Human-readable name for the source")
    source_type: str | None = Field(
        default=None, description="Source type (csv/json/api). Auto-detected if not provided"
    )
    field_mapping: dict[str, str] | None = Field(
        default=None, description="Optional mapping from source fields to standard fields"
    )


@app.post("/api/data/acquire")
async def acquire_data(request: AcquireDataRequest):
    """
    Trigger data acquisition from a source.

    Acquires data from CSV, JSON, or API source, normalizes it, and stores it in the database.
    """
    pipeline = DataAcquisitionPipeline()
    try:
        result = pipeline.process(
            source=request.source,
            source_name=request.source_name,
            source_type=request.source_type,
            field_mapping=request.field_mapping,
        )
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error("Error acquiring data: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error acquiring data: {str(e)}")


@app.get("/api/data/sources")
async def list_data_sources():
    """List all data sources."""
    with get_session() as session:
        repo = DataSourceRepository(session)
        sources = repo.list_all()
        return {
            "sources": [
                {
                    "id": s.id,
                    "name": s.name,
                    "type": s.type,
                    "url": s.url,
                    "last_updated": s.last_updated.isoformat() if s.last_updated else None,
                    "metadata": s.metadata,
                }
                for s in sources
            ]
        }


@app.get("/api/data/regions")
async def list_regions(query: str | None = None):
    """
    List available regions.

    Args:
        query: Optional search query to filter regions by code or name
    """
    with get_session() as session:
        repo = RegionRepository(session)
        if query:
            regions = repo.search(query)
        else:
            regions = repo.list_all()
        return {
            "regions": [
                {
                    "id": r.id,
                    "code": r.code,
                    "name": r.name,
                    "level": r.level,
                    "parent_region_id": r.parent_region_id,
                }
                for r in regions
            ]
        }


@app.get("/api/data/demographics")
async def query_demographics(
    region_id: int | None = None,
    region_code: str | None = None,
    year: int | None = None,
    gender: str | None = None,
    age_min: int | None = None,
    age_max: int | None = None,
    limit: int | None = Field(default=1000, le=10000),
):
    """
    Query demographic data with filters.

    Args:
        region_id: Filter by region ID
        region_code: Filter by region code
        year: Filter by year
        gender: Filter by gender (M/F/O/Total)
        age_min: Filter by minimum age
        age_max: Filter by maximum age
        limit: Maximum number of results (default: 1000, max: 10000)
    """
    with get_session() as session:
        repo = DemographicRepository(session)
        data = repo.query(
            region_id=region_id,
            region_code=region_code,
            year=year,
            gender=gender,
            age_min=age_min,
            age_max=age_max,
            limit=limit,
        )
        return {
            "count": len(data),
            "data": [
                {
                    "id": d.id,
                    "region_id": d.region_id,
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


@app.get("/api/data/stats")
async def get_statistics(region_id: int | None = None, year: int | None = None):
    """
    Get database statistics.

    Args:
        region_id: Optional region ID to filter statistics
        year: Optional year to filter statistics
    """
    with get_session() as session:
        demo_repo = DemographicRepository(session)
        source_repo = DataSourceRepository(session)
        region_repo = RegionRepository(session)

        stats = demo_repo.get_statistics(region_id=region_id, year=year)

        return {
            "total_sources": len(source_repo.list_all()),
            "total_regions": len(region_repo.list_all()),
            "demographics": stats,
        }


if __name__ == "__main__":
    init_app()
    main()
