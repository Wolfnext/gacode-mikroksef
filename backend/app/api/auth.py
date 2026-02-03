"""Authentication endpoints."""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, status

from app.config import get_settings
from app.models.auth import (
    InitTokenRequest,
    SessionResponse,
    SessionStatusResponse,
)
from app.services.session_manager import session_manager
from app.utils.exceptions import KSeFAuthError, KSeFSessionError, KSeFAPIError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/session/init-token",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initialize KSeF session",
    description="Initialize a KSeF session using encrypted token authentication.",
)
async def init_token_session(request: InitTokenRequest) -> SessionResponse:
    """
    Initialize a KSeF session using encrypted token authentication.

    Requires a valid KSeF authorization token to be configured in the environment.
    The token will be encrypted and sent to KSeF to establish a session.
    """
    settings = get_settings()

    if not settings.ksef_auth_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="KSeF authorization token not configured. Set KSEF_AUTH_TOKEN in .env",
        )

    try:
        session = await session_manager.init_session_with_token(nip=request.nip)

        logger.info(f"Session initialized for NIP: {request.nip}")

        return SessionResponse(
            sessionToken=session.token,
            referenceNumber=session.reference_number,
            timestamp=session.created_at,
        )

    except KSeFAuthError as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except KSeFAPIError as e:
        logger.error(f"KSeF API error: {e}")
        raise HTTPException(
            status_code=e.status_code or status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Session initialization failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize session: {str(e)}",
        )


@router.get(
    "/session/status",
    response_model=SessionStatusResponse,
    summary="Get session status",
    description="Get the status of the current KSeF session.",
)
async def get_session_status() -> SessionStatusResponse:
    """
    Get current session status.

    Returns information about the active session including
    processing state and invoice count.
    """
    session = session_manager.current_session

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active session",
        )

    # Optionally fetch fresh status from KSeF
    try:
        ksef_status = await session_manager.get_status()
        if ksef_status:
            return SessionStatusResponse(
                referenceNumber=ksef_status.get("referenceNumber", session.reference_number),
                processingCode=ksef_status.get("processingCode", 200),
                processingDescription=ksef_status.get("processingDescription", "Active"),
                numberOfElements=ksef_status.get("numberOfElements", 0),
                timestamp=datetime.utcnow(),
                isActive=True,
            )
    except Exception as e:
        logger.warning(f"Could not fetch KSeF status: {e}")

    # Return cached session info
    return SessionStatusResponse(
        referenceNumber=session.reference_number,
        processingCode=session.processing_code,
        processingDescription="Active" if session.is_valid else "Expired",
        numberOfElements=session.invoice_count,
        timestamp=datetime.utcnow(),
        isActive=session.is_valid,
    )


@router.post(
    "/session/terminate",
    status_code=status.HTTP_200_OK,
    summary="Terminate session",
    description="Terminate the current KSeF session.",
)
async def terminate_session():
    """
    Terminate the current KSeF session.

    This will invalidate the session token and clean up local state.
    """
    if not session_manager.current_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active session to terminate",
        )

    try:
        success = await session_manager.terminate()

        if success:
            logger.info("Session terminated successfully")
            return {"message": "Session terminated successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to terminate session",
            )

    except Exception as e:
        logger.error(f"Session termination error: {e}")
        # Still consider it terminated locally
        return {"message": "Session terminated (with warnings)", "warning": str(e)}


@router.get(
    "/session/info",
    summary="Get session info",
    description="Get detailed information about the current session.",
)
async def get_session_info():
    """
    Get detailed session information.

    Returns all available information about the current session
    including timing and state details.
    """
    info = session_manager.get_session_info()

    if not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active session",
        )

    return info
