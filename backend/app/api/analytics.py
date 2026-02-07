"""Analytics and reporting endpoints."""

import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, Query

from app.models.analytics import (
    AnalyticsSummary,
    MonthlyTurnover,
    InvoiceTypeSummary,
    TopCounterparty,
)
from app.services import database as db

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "",
    response_model=AnalyticsSummary,
    summary="Get analytics",
    description="Get comprehensive analytics including turnover and summaries.",
)
async def get_analytics(
    date_from: Optional[date] = Query(default=None, alias="dateFrom"),
    date_to: Optional[date] = Query(default=None, alias="dateTo"),
    months: int = Query(default=12, ge=1, le=36),
) -> AnalyticsSummary:
    date_from_str = date_from.isoformat() if date_from else None
    date_to_str = date_to.isoformat() if date_to else None

    totals = await db.get_totals(date_from_str, date_to_str)
    turnover_rows = await db.get_monthly_turnover(months, date_from_str, date_to_str)
    type_rows = await db.get_invoice_type_summary(None, date_from_str, date_to_str)
    top_issued = await db.get_top_counterparties(True, 10, date_from_str, date_to_str)
    top_received = await db.get_top_counterparties(False, 10, date_from_str, date_to_str)

    return AnalyticsSummary(
        invoiceCount=totals.get("invoice_count", 0),
        totalIssued=totals.get("total_issued", 0) or 0,
        totalReceived=totals.get("total_received", 0) or 0,
        monthlyTurnover=[
            MonthlyTurnover(
                month=row["month"],
                issuedCount=row.get("issued_count", 0),
                issuedNet=row.get("issued_net", 0) or 0,
                issuedGross=row.get("issued_gross", 0) or 0,
                receivedCount=row.get("received_count", 0),
                receivedNet=row.get("received_net", 0) or 0,
                receivedGross=row.get("received_gross", 0) or 0,
            )
            for row in turnover_rows
        ],
        typeSummary=[
            InvoiceTypeSummary(
                invoiceType=row.get("invoice_type", "VAT"),
                count=row.get("count", 0),
                netTotal=row.get("net_total", 0) or 0,
                vatTotal=row.get("vat_total", 0) or 0,
                grossTotal=row.get("gross_total", 0) or 0,
            )
            for row in type_rows
        ],
        topIssuedCounterparties=[
            TopCounterparty(
                nip=row.get("nip", ""),
                name=row.get("name", ""),
                invoiceCount=row.get("invoice_count", 0),
                totalGross=row.get("total_gross", 0) or 0,
            )
            for row in top_issued
        ],
        topReceivedCounterparties=[
            TopCounterparty(
                nip=row.get("nip", ""),
                name=row.get("name", ""),
                invoiceCount=row.get("invoice_count", 0),
                totalGross=row.get("total_gross", 0) or 0,
            )
            for row in top_received
        ],
    )
