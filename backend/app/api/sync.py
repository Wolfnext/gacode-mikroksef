"""Sync endpoints for invoice synchronization."""

import logging
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.models.invoice import InvoiceSyncRequest, InvoiceSyncResponse, SubjectType
from app.services.invoice_service import invoice_service
from app.services.session_manager import session_manager
from app.services import database as db
from app.utils.exceptions import KSeFSessionError, KSeFAPIError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "",
    response_model=InvoiceSyncResponse,
    summary="Sync invoices from KSeF",
    description="Synchronize invoices from KSeF to local cache.",
)
async def sync_invoices(request: InvoiceSyncRequest) -> InvoiceSyncResponse:
    """
    Sync invoices from KSeF to local cache.

    This operation fetches invoices from KSeF and stores them locally
    for faster access and offline viewing.

    - subject_type: Which invoices to sync (issued/received)
    - date_from/date_to: Optional date range filter
    - full_sync: If true, clears existing cache before syncing
    """
    if not session_manager.has_active_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No active KSeF session. Please authenticate first.",
        )

    try:
        result = await invoice_service.sync_invoices(
            subject_type=request.subject_type,
            date_from=request.date_from,
            date_to=request.date_to,
            full_sync=request.full_sync,
        )

        return InvoiceSyncResponse(
            status=result["status"],
            totalFetched=result["total_fetched"],
            newInvoices=result["new_invoices"],
            updatedInvoices=result["updated_invoices"],
            errors=result.get("errors", []),
            startedAt=result["started_at"],
            completedAt=result.get("completed_at"),
        )

    except KSeFSessionError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except KSeFAPIError as e:
        logger.error(f"KSeF API error during sync: {e}")
        raise HTTPException(
            status_code=e.status_code or status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Sync failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}",
        )


@router.get(
    "/status",
    summary="Get sync status",
    description="Get the status of the last sync operation.",
)
async def get_sync_status(
    sync_type: SubjectType = Query(
        default=SubjectType.SUBJECT1,
        alias="syncType",
        description="Type of sync to check status for",
    ),
):
    """
    Get the status of the last sync operation.

    Returns information about when the last sync completed
    and how many invoices were processed.
    """
    last_sync = await db.get_last_sync(f"sync_{sync_type.value}")

    if not last_sync:
        return {
            "status": "never_synced",
            "message": "No sync has been performed yet",
            "syncType": sync_type.value,
        }

    return {
        "status": last_sync.get("status"),
        "syncType": sync_type.value,
        "startedAt": last_sync.get("started_at"),
        "completedAt": last_sync.get("completed_at"),
        "totalFetched": last_sync.get("total_fetched", 0),
        "newInvoices": last_sync.get("new_invoices", 0),
        "updatedInvoices": last_sync.get("updated_invoices", 0),
        "lastAcquisitionTimestamp": last_sync.get("last_acquisition_timestamp"),
    }


@router.delete(
    "/cache",
    summary="Clear invoice cache",
    description="Clear all cached invoices from local database.",
)
async def clear_cache():
    """
    Clear the local invoice cache.

    This removes all cached invoices from the local database.
    Use this before a full re-sync or to free up space.
    """
    try:
        deleted_count = await db.clear_invoice_cache()
        logger.info(f"Cleared {deleted_count} invoices from cache")

        return {
            "status": "success",
            "message": f"Cleared {deleted_count} invoices from cache",
            "deletedCount": deleted_count,
        }

    except Exception as e:
        logger.error(f"Failed to clear cache: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}",
        )


@router.post(
    "/issued",
    response_model=InvoiceSyncResponse,
    summary="Sync issued invoices",
    description="Sync issued invoices (where you are the seller).",
)
async def sync_issued_invoices(
    date_from: Optional[date] = Query(default=None, alias="dateFrom"),
    date_to: Optional[date] = Query(default=None, alias="dateTo"),
    full_sync: bool = Query(default=False, alias="fullSync"),
) -> InvoiceSyncResponse:
    """
    Sync issued invoices (as seller).

    Convenience endpoint for syncing invoices where your company is the seller.
    """
    request = InvoiceSyncRequest(
        subjectType=SubjectType.SUBJECT1,
        dateFrom=date_from,
        dateTo=date_to,
        fullSync=full_sync,
    )
    return await sync_invoices(request)


@router.post(
    "/received",
    response_model=InvoiceSyncResponse,
    summary="Sync received invoices",
    description="Sync received invoices (where you are the buyer).",
)
async def sync_received_invoices(
    date_from: Optional[date] = Query(default=None, alias="dateFrom"),
    date_to: Optional[date] = Query(default=None, alias="dateTo"),
    full_sync: bool = Query(default=False, alias="fullSync"),
) -> InvoiceSyncResponse:
    """
    Sync received invoices (as buyer).

    Convenience endpoint for syncing invoices where your company is the buyer.
    """
    request = InvoiceSyncRequest(
        subjectType=SubjectType.SUBJECT2,
        dateFrom=date_from,
        dateTo=date_to,
        fullSync=full_sync,
    )
    return await sync_invoices(request)
