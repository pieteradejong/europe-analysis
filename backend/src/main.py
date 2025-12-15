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


if __name__ == "__main__":
    init_app()
    main()
