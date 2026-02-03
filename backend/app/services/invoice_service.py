"""
Invoice Service
Business logic for invoice operations.
"""

import logging
from datetime import datetime, date, time, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.services.ksef_client import ksef_client
from app.services.session_manager import session_manager
from app.services import database as db
from app.models.invoice import (
    InvoiceHeader,
    InvoiceListResponse,
    InvoiceQueryParams,
    SubjectType,
    InvoiceType,
)
from app.utils.exceptions import KSeFSessionError

logger = logging.getLogger(__name__)


class InvoiceService:
    """Service for invoice operations."""

    _SUBJECT_TYPE_MAP = {
        SubjectType.SUBJECT1: "Subject1",
        SubjectType.SUBJECT2: "Subject2",
        SubjectType.SUBJECT3: "Subject3",
    }

    _INVOICE_TYPE_TO_V2 = {
        "VAT": "Vat",
        "KOR": "Kor",
        "ZAL": "Zal",
        "ROZ": "Roz",
    }

    _INVOICE_TYPE_FROM_V2 = {
        "Vat": "VAT",
        "Zal": "ZAL",
        "Kor": "KOR",
        "Roz": "ROZ",
        "Upr": "VAT",
        "KorZal": "KOR",
        "KorRoz": "KOR",
        "VatPef": "VAT",
        "VatPefSp": "VAT",
        "KorPef": "KOR",
        "VatRr": "VAT",
        "KorVatRr": "KOR",
    }

    def _map_subject_type(self, subject_type: SubjectType) -> str:
        return self._SUBJECT_TYPE_MAP.get(subject_type, "Subject1")

    def _map_invoice_type_to_v2(self, invoice_type: str) -> str:
        return self._INVOICE_TYPE_TO_V2.get(invoice_type, invoice_type)

    def _map_invoice_type_from_v2(self, invoice_type: Optional[str]) -> str:
        if not invoice_type:
            return "VAT"
        if invoice_type in self._INVOICE_TYPE_TO_V2:
            return invoice_type
        mapped = self._INVOICE_TYPE_FROM_V2.get(invoice_type)
        return mapped or "VAT"

    def _build_date_range(
        self,
        *,
        date_type: str,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        from_datetime: Optional[datetime] = None,
        default_days: int = 30,
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)

        if from_datetime:
            from_dt = from_datetime
            if from_dt.tzinfo is None:
                from_dt = from_dt.replace(tzinfo=timezone.utc)
        elif date_from:
            from_dt = datetime.combine(date_from, time.min, tzinfo=timezone.utc)
        else:
            from_dt = now - timedelta(days=default_days)

        date_range: Dict[str, Any] = {
            "dateType": date_type,
            "from": from_dt.isoformat(),
        }

        if date_to:
            to_dt = datetime.combine(date_to, time.max, tzinfo=timezone.utc)
            date_range["to"] = to_dt.isoformat()

        return date_range

    def _build_v2_query_filters(
        self,
        params: InvoiceQueryParams,
        *,
        for_sync: bool = False,
        acquisition_from: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        subject_type = self._map_subject_type(params.subject_type)

        if for_sync:
            date_type = "PermanentStorage"
        else:
            date_type = "Issue" if params.date_from or params.date_to else "PermanentStorage"

        date_range = self._build_date_range(
            date_type=date_type,
            date_from=params.date_from,
            date_to=params.date_to,
            from_datetime=None if params.date_from else acquisition_from,
        )

        filters: Dict[str, Any] = {
            "subjectType": subject_type,
            "dateRange": date_range,
        }

        if params.nip_filter:
            if params.subject_type == SubjectType.SUBJECT1:
                filters["buyerIdentifier"] = {
                    "type": "Nip",
                    "value": params.nip_filter,
                }
            else:
                filters["sellerNip"] = params.nip_filter

        if params.amount_from is not None or params.amount_to is not None:
            amount_filter: Dict[str, Any] = {"type": "Brutto"}
            if params.amount_from is not None:
                amount_filter["from"] = float(params.amount_from)
            if params.amount_to is not None:
                amount_filter["to"] = float(params.amount_to)
            filters["amount"] = amount_filter

        if params.invoice_type:
            filters["invoiceTypes"] = [
                self._map_invoice_type_to_v2(params.invoice_type.value)
            ]

        return filters

    def _parse_ksef_invoice(self, ksef_data: Dict, is_issued: bool = True) -> Dict[str, Any]:
        """Parse KSeF invoice response to database format."""
        if "ksefNumber" in ksef_data or "seller" in ksef_data:
            return self._parse_ksef_v2_metadata(ksef_data, is_issued)
        return self._parse_ksef_legacy(ksef_data, is_issued)

    def _parse_ksef_v2_metadata(self, ksef_data: Dict, is_issued: bool) -> Dict[str, Any]:
        seller = ksef_data.get("seller") or {}
        buyer = ksef_data.get("buyer") or {}
        buyer_identifier = buyer.get("identifier") or {}

        invoice_type = self._map_invoice_type_from_v2(ksef_data.get("invoiceType"))

        issue_date = ksef_data.get("issueDate")
        invoicing_date = issue_date or ksef_data.get("invoicingDate")
        acquisition_timestamp = (
            ksef_data.get("acquisitionDate") or ksef_data.get("permanentStorageDate")
        )

        return {
            "ksef_reference_number": ksef_data.get("ksefNumber", ""),
            "invoice_reference_number": ksef_data.get("invoiceNumber", ""),
            "invoicing_date": invoicing_date,
            "acquisition_timestamp": acquisition_timestamp,
            "subject_by_nip": seller.get("nip", ""),
            "subject_by_name": seller.get("name", ""),
            "subject_to_nip": buyer_identifier.get("value", "") if buyer_identifier else "",
            "subject_to_name": buyer.get("name", "") if buyer else "",
            "net_amount": str(ksef_data.get("netAmount", 0)),
            "vat_amount": str(ksef_data.get("vatAmount", 0)),
            "gross_amount": str(ksef_data.get("grossAmount", 0)),
            "currency": ksef_data.get("currency", "PLN"),
            "invoice_type": invoice_type,
            "schema_version": None,
            "hash_value": ksef_data.get("invoiceHash", "") or "",
            "is_issued": is_issued,
        }

    def _parse_ksef_legacy(self, ksef_data: Dict, is_issued: bool) -> Dict[str, Any]:
        subject_by = ksef_data.get("subjectBy", {})
        subject_to = ksef_data.get("subjectTo", {})

        # Extract identifiers
        subject_by_id = subject_by.get("issuedByIdentifier", {})
        subject_to_id = subject_to.get("issuedToIdentifier", {}) if subject_to else {}

        # Parse hash
        invoice_hash = ksef_data.get("invoiceHash", {})
        hash_sha = invoice_hash.get("hashSHA", {}) if invoice_hash else {}

        return {
            "ksef_reference_number": ksef_data.get("ksefReferenceNumber", ""),
            "invoice_reference_number": ksef_data.get("invoiceReferenceNumber", ""),
            "invoicing_date": ksef_data.get("invoicingDate"),
            "acquisition_timestamp": ksef_data.get("acquisitionTimestamp"),
            "subject_by_nip": subject_by_id.get("identifier", ""),
            "subject_by_name": subject_by.get("issuedByName", {}).get("fullName", ""),
            "subject_to_nip": subject_to_id.get("identifier", "") if subject_to_id else "",
            "subject_to_name": subject_to.get("issuedToName", {}).get("fullName", "") if subject_to else "",
            "net_amount": str(ksef_data.get("net", 0)),
            "vat_amount": str(ksef_data.get("vat", 0)),
            "gross_amount": str(ksef_data.get("gross", 0)),
            "currency": ksef_data.get("currency", "PLN"),
            "invoice_type": ksef_data.get("invoiceType", "VAT"),
            "schema_version": ksef_data.get("schemaVersion"),
            "hash_value": hash_sha.get("value", ""),
            "is_issued": is_issued,
        }

    def _db_to_invoice_header(self, db_row: Dict) -> InvoiceHeader:
        """Convert database row to InvoiceHeader model."""
        return InvoiceHeader(
            invoiceReferenceNumber=db_row.get("invoice_reference_number", ""),
            ksefReferenceNumber=db_row.get("ksef_reference_number", ""),
            invoicingDate=db_row.get("invoicing_date"),
            acquisitionTimestamp=db_row.get("acquisition_timestamp") or datetime.utcnow(),
            subjectBy={
                "identifierType": "nip",
                "identifier": db_row.get("subject_by_nip", ""),
                "name": db_row.get("subject_by_name"),
            },
            subjectTo={
                "identifierType": "nip",
                "identifier": db_row.get("subject_to_nip", ""),
                "name": db_row.get("subject_to_name"),
            } if db_row.get("subject_to_nip") else None,
            net=Decimal(str(db_row.get("net_amount", 0))),
            vat=Decimal(str(db_row.get("vat_amount", 0))),
            gross=Decimal(str(db_row.get("gross_amount", 0))),
            currency=db_row.get("currency", "PLN"),
            schemaVersion=db_row.get("schema_version"),
            invoiceType=InvoiceType(db_row.get("invoice_type", "VAT")),
        )

    async def query_invoices_from_ksef(
        self, params: InvoiceQueryParams
    ) -> InvoiceListResponse:
        """Query invoices directly from KSeF API."""
        token = session_manager.require_session()

        filters = self._build_v2_query_filters(params)

        ksef_page_size = max(10, params.page_size)
        ksef_page_offset = params.page_offset // ksef_page_size

        # Execute query
        response = await ksef_client.query_invoices(
            token,
            filters,
            page_offset=ksef_page_offset,
            page_size=ksef_page_size,
        )

        # Parse response (v2 returns "invoices")
        invoice_list = response.get("invoices")
        if invoice_list is None:
            invoice_list = response.get("invoiceHeaderList", [])
        is_issued = params.subject_type == SubjectType.SUBJECT1

        headers = []
        for inv_data in invoice_list:
            try:
                parsed = self._parse_ksef_invoice(inv_data, is_issued)
                # Cache to database
                await db.save_invoice(parsed)
                headers.append(self._db_to_invoice_header(parsed))
            except Exception as e:
                logger.warning(f"Failed to parse invoice: {e}")

        has_more = response.get("hasMore")
        if has_more is None:
            has_more = len(invoice_list) >= ksef_page_size

        return InvoiceListResponse(
            timestamp=datetime.utcnow(),
            referenceNumber=response.get("referenceNumber", "ksef_query"),
            numberOfElements=len(headers),
            pageSize=ksef_page_size,
            pageOffset=params.page_offset,
            hasMore=bool(has_more),
            invoiceHeaderList=headers,
        )

    async def get_invoices_from_cache(
        self, params: InvoiceQueryParams
    ) -> InvoiceListResponse:
        """Get invoices from local cache."""
        is_issued = params.subject_type == SubjectType.SUBJECT1

        # Count total
        total = await db.count_invoices(
            is_issued=is_issued,
            date_from=params.date_from.isoformat() if params.date_from else None,
            date_to=params.date_to.isoformat() if params.date_to else None,
            nip_filter=params.nip_filter,
            invoice_type=params.invoice_type.value if params.invoice_type else None,
        )

        # Fetch page
        rows = await db.get_invoices(
            is_issued=is_issued,
            date_from=params.date_from.isoformat() if params.date_from else None,
            date_to=params.date_to.isoformat() if params.date_to else None,
            nip_filter=params.nip_filter,
            invoice_type=params.invoice_type.value if params.invoice_type else None,
            limit=params.page_size,
            offset=params.page_offset,
        )

        headers = [self._db_to_invoice_header(row) for row in rows]

        return InvoiceListResponse(
            timestamp=datetime.utcnow(),
            referenceNumber="cache",
            numberOfElements=total,
            pageSize=params.page_size,
            pageOffset=params.page_offset,
            hasMore=(params.page_offset + params.page_size) < total,
            invoiceHeaderList=headers,
        )

    async def get_invoice_detail(self, ksef_reference_number: str) -> Optional[Dict]:
        """Get invoice detail including XML content."""
        # First check cache
        cached = await db.get_invoice_by_ksef_ref(ksef_reference_number)

        if cached and cached.get("xml_content"):
            return {
                "header": self._db_to_invoice_header(cached),
                "xmlContent": cached.get("xml_content"),
                "upoAvailable": bool(cached.get("upo_reference")),
                "cachedAt": cached.get("cached_at"),
            }

        # Fetch from KSeF if we have a session
        if session_manager.has_active_session:
            try:
                xml_bytes = await ksef_client.get_invoice(
                    session_manager.session_token,
                    ksef_reference_number,
                )
                xml_content = xml_bytes.decode("utf-8")

                # Update cache
                await db.update_invoice_xml(ksef_reference_number, xml_content)

                if cached:
                    return {
                        "header": self._db_to_invoice_header(cached),
                        "xmlContent": xml_content,
                        "upoAvailable": bool(cached.get("upo_reference")),
                        "cachedAt": datetime.utcnow(),
                    }
            except Exception as e:
                logger.error(f"Failed to fetch invoice from KSeF: {e}")

        if cached:
            return {
                "header": self._db_to_invoice_header(cached),
                "xmlContent": None,
                "upoAvailable": bool(cached.get("upo_reference")),
                "cachedAt": cached.get("cached_at"),
            }

        return None

    async def download_invoice_xml(self, ksef_reference_number: str) -> Optional[bytes]:
        """Download invoice XML content."""
        # Check cache first
        cached = await db.get_invoice_by_ksef_ref(ksef_reference_number)
        if cached and cached.get("xml_content"):
            return cached["xml_content"].encode("utf-8")

        # Fetch from KSeF
        if session_manager.has_active_session:
            try:
                xml_bytes = await ksef_client.get_invoice(
                    session_manager.session_token,
                    ksef_reference_number,
                )
                # Cache it
                await db.update_invoice_xml(
                    ksef_reference_number,
                    xml_bytes.decode("utf-8"),
                )
                return xml_bytes
            except Exception as e:
                logger.error(f"Failed to download invoice: {e}")
                raise

        raise KSeFSessionError("No active session to download invoice")

    async def sync_invoices(
        self,
        subject_type: SubjectType = SubjectType.SUBJECT1,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        full_sync: bool = False,
    ) -> Dict[str, Any]:
        """
        Sync invoices from KSeF to local cache.

        Args:
            subject_type: Which invoices to sync (issued/received)
            date_from: Start date filter
            date_to: End date filter
            full_sync: If True, clear cache before syncing

        Returns:
            Sync status information
        """
        token = session_manager.require_session()

        sync_id = await db.create_sync_record(f"sync_{subject_type.value}")
        started_at = datetime.utcnow()

        stats = {
            "status": "running",
            "total_fetched": 0,
            "new_invoices": 0,
            "updated_invoices": 0,
            "errors": [],
        }

        try:
            if full_sync:
                await db.clear_invoice_cache()
                logger.info("Cache cleared for full sync")

            # Determine start timestamp
            acquisition_from: Optional[datetime] = None
            if not full_sync:
                last_sync = await db.get_last_sync(f"sync_{subject_type.value}")
                if last_sync and last_sync.get("last_acquisition_timestamp"):
                    last_value = last_sync["last_acquisition_timestamp"]
                    if isinstance(last_value, datetime):
                        acquisition_from = last_value
                    else:
                        try:
                            acquisition_from = datetime.fromisoformat(
                                str(last_value).replace("Z", "+00:00")
                            )
                        except Exception:
                            acquisition_from = None

            # Build query filters (v2)
            params = InvoiceQueryParams(
                subjectType=subject_type,
                dateFrom=date_from,
                dateTo=date_to,
            )
            filters = self._build_v2_query_filters(
                params,
                for_sync=True,
                acquisition_from=acquisition_from,
            )

            # Paginate through all results (pageOffset is page index in v2)
            page_offset = 0
            page_size = 100
            last_acquisition = None
            is_issued = subject_type == SubjectType.SUBJECT1

            while True:
                response = await ksef_client.query_invoices(
                    token,
                    filters,
                    page_offset=page_offset,
                    page_size=page_size,
                )
                invoice_list = response.get("invoices")
                if invoice_list is None:
                    invoice_list = response.get("invoiceHeaderList", [])

                if not invoice_list:
                    break

                for inv_data in invoice_list:
                    try:
                        parsed = self._parse_ksef_invoice(inv_data, is_issued)

                        # Check if exists
                        existing = await db.get_invoice_by_ksef_ref(
                            parsed["ksef_reference_number"]
                        )

                        await db.save_invoice(parsed)
                        stats["total_fetched"] += 1

                        if existing:
                            stats["updated_invoices"] += 1
                        else:
                            stats["new_invoices"] += 1

                        # Track last acquisition timestamp
                        if parsed.get("acquisition_timestamp"):
                            acq = parsed["acquisition_timestamp"]
                            if isinstance(acq, str):
                                acq = datetime.fromisoformat(acq.replace("Z", "+00:00"))
                            if last_acquisition is None or acq > last_acquisition:
                                last_acquisition = acq

                    except Exception as e:
                        logger.warning(f"Failed to process invoice: {e}")
                        stats["errors"].append(str(e))

                has_more = response.get("hasMore")
                if has_more is None:
                    has_more = len(invoice_list) >= page_size

                if not has_more:
                    break

                page_offset += 1

            stats["status"] = "completed"

            # Update sync record
            await db.update_sync_record(
                sync_id,
                status="completed",
                total_fetched=stats["total_fetched"],
                new_invoices=stats["new_invoices"],
                updated_invoices=stats["updated_invoices"],
                last_acquisition=last_acquisition,
            )

        except Exception as e:
            logger.error(f"Sync failed: {e}")
            stats["status"] = "failed"
            stats["errors"].append(str(e))

            await db.update_sync_record(
                sync_id,
                status="failed",
                total_fetched=stats["total_fetched"],
                new_invoices=stats["new_invoices"],
                updated_invoices=stats["updated_invoices"],
                errors=str(stats["errors"]),
            )

        stats["started_at"] = started_at
        stats["completed_at"] = datetime.utcnow()
        return stats


# Singleton instance
invoice_service = InvoiceService()
