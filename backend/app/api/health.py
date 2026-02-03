"""Health check endpoints."""

import logging
from datetime import datetime

from fastapi import APIRouter

from app.config import get_settings
from app.models.common import HealthResponse
from app.services.session_manager import session_manager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Check API health status.

    Returns current session state and configuration info.
    """
    settings = get_settings()
    session = session_manager.current_session

    return HealthResponse(
        status="healthy",
        environment=settings.ksef_environment,
        ksefApi=settings.effective_ksef_url,
        sessionActive=session is not None,
        sessionReference=session.reference_number if session else None,
        databaseConnected=True,
        timestamp=datetime.utcnow(),
        version="1.0.0",
    )


@router.get("/ready")
async def readiness_check():
    """
    Kubernetes-style readiness probe.

    Returns 200 if the service is ready to accept traffic.
    """
    return {"status": "ready"}


@router.get("/live")
async def liveness_check():
    """
    Kubernetes-style liveness probe.

    Returns 200 if the service is alive.
    """
    return {"status": "live"}
