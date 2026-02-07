"""
mikroKSeF Backend - FastAPI Application
Main entry point for the application.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.api.router import api_router
from app.services.database import init_database, close_database
from app.services.session_manager import session_manager

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup/shutdown events."""
    settings = get_settings()

    # Startup
    logger.info(f"Starting {settings.app_name}")
    logger.info(f"Environment: {settings.ksef_environment}")
    logger.info(f"KSeF API: {settings.effective_ksef_url}")

    # Initialize database
    await init_database()
    logger.info("Database initialized")

    # Start auto-sync scheduler
    from app.services.scheduler import sync_scheduler
    try:
        await sync_scheduler.start()
        logger.info("Auto-sync scheduler initialized")
    except Exception as e:
        logger.warning(f"Failed to start auto-sync scheduler: {e}")

    yield

    # Shutdown
    logger.info("Shutting down...")
    try:
        await sync_scheduler.stop()
    except Exception:
        pass
    await session_manager.close_all_sessions()
    await close_database()
    logger.info("Cleanup complete")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="mikroKSeF API",
        description="Local proxy for Poland's KSeF e-Invoice system",
        version="1.0.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API router
    app.include_router(api_router, prefix="/api")

    # Root endpoint
    @app.get("/", tags=["root"])
    async def root():
        """Root endpoint with API information."""
        return {
            "name": settings.app_name,
            "version": "1.0.0",
            "environment": settings.ksef_environment,
            "ksef_api": settings.effective_ksef_url,
            "docs": "/docs" if settings.debug else None,
        }

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "type": type(exc).__name__},
        )

    return app


# Create application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
