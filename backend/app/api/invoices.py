"""Invoice endpoints."""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import Response

from app.config import get_settings

from app.models.invoice import (
    InvoiceListResponse,
    InvoiceQueryParams,
    InvoiceStatusResponse,
    InvoiceDetail,
    SubjectType,
    InvoiceType,
)
from app.services.invoice_service import invoice_service
from app.services.session_manager import session_manager
from app.services.ksef_client import ksef_client
from app.services import database as db
from app.utils.exceptions import KSeFSessionError, KSeFAPIError

logger = logging.getLogger(__name__)
router = APIRouter()


def require_session() -> str:
    """Dependency to ensure active session exists."""
    if not session_manager.session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No active KSeF session. Please authenticate first.",
        )
    return session_manager.session_token


@router.get(
    "",
    response_model=InvoiceListResponse,
    summary="List invoices",
    description="List invoices from local cache with optional filters.",
)
async def list_invoices(
    subject_type: SubjectType = Query(
        default=SubjectType.SUBJECT1,
        alias="subjectType",
        description="subject1=issued (seller), subject2=received (buyer)",
    ),
    date_from: Optional[date] = Query(
        default=None,
        alias="dateFrom",
        description="Filter by invoicing date from",
    ),
    date_to: Optional[date] = Query(
        default=None,
        alias="dateTo",
        description="Filter by invoicing date to",
    ),
    amount_from: Optional[Decimal] = Query(
        default=None,
        alias="amountFrom",
        description="Filter by minimum gross amount",
    ),
    amount_to: Optional[Decimal] = Query(
        default=None,
        alias="amountTo",
        description="Filter by maximum gross amount",
    ),
    invoice_type: Optional[InvoiceType] = Query(
        default=None,
        alias="invoiceType",
        description="Filter by invoice type",
    ),
    nip_filter: Optional[str] = Query(
        default=None,
        alias="nipFilter",
        description="Filter by counterparty NIP",
    ),
    page_size: int = Query(default=50, ge=1, le=100, alias="pageSize"),
    page_offset: int = Query(default=0, ge=0, alias="pageOffset"),
    use_cache: bool = Query(
        default=True,
        alias="useCache",
        description="If true, use local cache. If false, query KSeF directly.",
    ),
) -> InvoiceListResponse:
    """
    List invoices with filters.

    By default, returns invoices from local cache. Set useCache=false
    to fetch directly from KSeF (requires active session).
    """
    params = InvoiceQueryParams(
        subjectType=subject_type,
        dateFrom=date_from,
        dateTo=date_to,
        amountFrom=amount_from,
        amountTo=amount_to,
        invoiceType=invoice_type,
        nipFilter=nip_filter,
        pageSize=page_size,
        pageOffset=page_offset,
    )

    if use_cache:
        return await invoice_service.get_invoices_from_cache(params)

    # Query KSeF directly
    try:
        require_session()
        return await invoice_service.query_invoices_from_ksef(params)
    except KSeFSessionError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except KSeFAPIError as e:
        raise HTTPException(
            status_code=e.status_code or status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to query invoices: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query invoices: {str(e)}",
        )


@router.get(
    "/search",
    response_model=InvoiceListResponse,
    summary="Search invoices",
    description="Full-text search across invoice metadata and content.",
)
async def search_invoices_endpoint(
    q: str = Query(..., min_length=2, description="Search query"),
    subject_type: Optional[SubjectType] = Query(
        default=None, alias="subjectType",
    ),
    page_size: int = Query(default=50, ge=1, le=100, alias="pageSize"),
    page_offset: int = Query(default=0, ge=0, alias="pageOffset"),
) -> InvoiceListResponse:
    """Search invoices using full-text search."""
    try:
        is_issued = None
        if subject_type == SubjectType.SUBJECT1:
            is_issued = True
        elif subject_type == SubjectType.SUBJECT2:
            is_issued = False

        total = await db.count_search_results(q, is_issued)
        rows = await db.search_invoices(q, is_issued, page_size, page_offset)
        headers = [invoice_service._db_to_invoice_header(row) for row in rows]

        return InvoiceListResponse(
            timestamp=datetime.utcnow(),
            referenceNumber="search",
            numberOfElements=total,
            pageSize=page_size,
            pageOffset=page_offset,
            hasMore=(page_offset + page_size) < total,
            invoiceHeaderList=headers,
        )
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )


@router.get(
    "/{ksef_reference_number}",
    response_model=InvoiceDetail,
    summary="Get invoice detail",
    description="Get detailed invoice information including XML content.",
)
async def get_invoice_detail(ksef_reference_number: str) -> InvoiceDetail:
    """
    Get detailed information about a specific invoice.

    Returns invoice header and XML content if available.
    """
    try:
        detail = await invoice_service.get_invoice_detail(ksef_reference_number)

        if not detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice not found: {ksef_reference_number}",
            )

        return InvoiceDetail(
            header=detail["header"],
            xmlContent=detail.get("xmlContent"),
            upoAvailable=detail.get("upoAvailable", False),
            cachedAt=detail.get("cachedAt"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get invoice detail: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get invoice: {str(e)}",
        )


@router.get(
    "/{ksef_reference_number}/download",
    summary="Download invoice XML",
    description="Download invoice as XML file.",
)
async def download_invoice(ksef_reference_number: str) -> Response:
    """
    Download invoice XML file.

    Returns the invoice in XML format as a downloadable file.
    """
    try:
        xml_content = await invoice_service.download_invoice_xml(ksef_reference_number)

        if not xml_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice XML not available: {ksef_reference_number}",
            )

        return Response(
            content=xml_content,
            media_type="application/xml",
            headers={
                "Content-Disposition": f'attachment; filename="{ksef_reference_number}.xml"'
            },
        )

    except KSeFSessionError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download invoice: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download invoice: {str(e)}",
        )


@router.get(
    "/{ksef_reference_number}/status",
    response_model=InvoiceStatusResponse,
    summary="Get invoice status",
    description="Get the processing status of a specific invoice.",
)
async def get_invoice_status(ksef_reference_number: str) -> InvoiceStatusResponse:
    """
    Get invoice processing status from KSeF.

    Requires active session.
    """
    token = require_session()

    try:
        status_response = await ksef_client.get_invoice_status(
            token, ksef_reference_number
        )

        return InvoiceStatusResponse(
            processingCode=status_response.get("processingCode", 200),
            processingDescription=status_response.get("processingDescription"),
            ksefReferenceNumber=status_response.get("ksefReferenceNumber"),
            timestamp=status_response.get("timestamp"),
            acquisitionTimestamp=status_response.get("acquisitionTimestamp"),
            upoReferenceNumber=status_response.get("upoReferenceNumber"),
        )

    except KSeFAPIError as e:
        raise HTTPException(
            status_code=e.status_code or status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to get invoice status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get invoice status: {str(e)}",
        )


@router.get(
    "/{ksef_reference_number}/upo",
    summary="Download UPO",
    description="Download official confirmation (UPO) for an invoice.",
)
async def download_upo(ksef_reference_number: str) -> Response:
    """
    Download UPO (Urzędowe Poświadczenie Odbioru).

    Returns the official confirmation document for the invoice.
    Requires active session.
    """
    token = require_session()

    try:
        # First get invoice status to find UPO reference
        status_response = await ksef_client.get_invoice_status(
            token, ksef_reference_number
        )

        upo_ref = status_response.get("upoReferenceNumber")
        if not upo_ref:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="UPO not available for this invoice",
            )

        session_ref = session_manager.current_session.reference_number
        upo_content = await ksef_client.download_upo(token, session_ref, upo_ref)

        return Response(
            content=upo_content,
            media_type="application/xml",
            headers={
                "Content-Disposition": f'attachment; filename="UPO_{ksef_reference_number}.xml"'
            },
        )

    except HTTPException:
        raise
    except KSeFAPIError as e:
        raise HTTPException(
            status_code=e.status_code or status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to download UPO: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download UPO: {str(e)}",
        )


@router.get(
    "/{ksef_reference_number}/pdf",
    summary="Download invoice PDF",
    description="Generate and download invoice as PDF.",
)
async def download_invoice_pdf(ksef_reference_number: str) -> Response:
    """Generate PDF visualization of an invoice via the PDF microservice."""
    try:
        xml_content = await invoice_service.download_invoice_xml(ksef_reference_number)

        if not xml_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice XML not available: {ksef_reference_number}",
            )

        settings = get_settings()

        from app.utils.qr_generator import generate_ksef_qr_url
        qr_url = generate_ksef_qr_url(ksef_reference_number, settings.ksef_environment)

        async with httpx.AsyncClient(timeout=30.0) as client:
            pdf_response = await client.post(
                f"{settings.pdf_service_url}/generate-invoice",
                content=xml_content if isinstance(xml_content, bytes) else xml_content.encode("utf-8"),
                headers={
                    "Content-Type": "application/xml",
                    "X-KSeF-Reference": ksef_reference_number,
                    "X-QR-Code": qr_url,
                },
            )

        if pdf_response.status_code != 200:
            logger.error(f"PDF service error: {pdf_response.status_code} {pdf_response.text}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="PDF generation service returned an error",
            )

        return Response(
            content=pdf_response.content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{ksef_reference_number}.pdf"'
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate invoice PDF: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate invoice PDF: {str(e)}",
        )


@router.get(
    "/{ksef_reference_number}/upo-pdf",
    summary="Download UPO as PDF",
    description="Generate and download UPO as PDF.",
)
async def download_upo_pdf(ksef_reference_number: str) -> Response:
    """Generate PDF visualization of UPO document via the PDF microservice."""
    token = require_session()

    try:
        status_response = await ksef_client.get_invoice_status(
            token, ksef_reference_number
        )

        upo_ref = status_response.get("upoReferenceNumber")
        if not upo_ref:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="UPO not available for this invoice",
            )

        session_ref = session_manager.current_session.reference_number
        upo_content = await ksef_client.download_upo(token, session_ref, upo_ref)

        settings = get_settings()
        async with httpx.AsyncClient(timeout=30.0) as client:
            pdf_response = await client.post(
                f"{settings.pdf_service_url}/generate-upo",
                content=upo_content if isinstance(upo_content, bytes) else upo_content.encode("utf-8"),
                headers={
                    "Content-Type": "application/xml",
                    "X-KSeF-Reference": ksef_reference_number,
                },
            )

        if pdf_response.status_code != 200:
            logger.error(f"UPO PDF service error: {pdf_response.status_code} {pdf_response.text}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="UPO PDF generation service returned an error",
            )

        return Response(
            content=pdf_response.content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="UPO_{ksef_reference_number}.pdf"'
            },
        )

    except HTTPException:
        raise
    except KSeFAPIError as e:
        raise HTTPException(
            status_code=e.status_code or status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to generate UPO PDF: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate UPO PDF: {str(e)}",
        )
