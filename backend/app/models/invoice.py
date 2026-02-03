"""Invoice-related Pydantic models."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class InvoiceType(str, Enum):
    """Type of invoice."""

    VAT = "VAT"
    CORRECTION = "KOR"
    ADVANCE = "ZAL"
    SETTLEMENT = "ROZ"


class SubjectType(str, Enum):
    """Subject role in invoice context."""

    SUBJECT1 = "subject1"  # Seller
    SUBJECT2 = "subject2"  # Buyer
    SUBJECT3 = "subject3"  # Third party


class HashSHA(BaseModel):
    """SHA hash specification."""

    algorithm: str = Field(default="SHA-256")
    encoding: str = Field(default="Base64")
    value: str = Field(..., description="Base64-encoded hash value")


class SubjectInfo(BaseModel):
    """Subject (company/person) information."""

    identifier_type: str = Field(..., alias="identifierType")
    identifier: str = Field(..., description="NIP or other identifier")
    name: Optional[str] = Field(None, description="Subject name")
    trade_name: Optional[str] = Field(None, alias="tradeName")

    class Config:
        populate_by_name = True


class InvoiceHeader(BaseModel):
    """Invoice header/summary information."""

    invoice_reference_number: str = Field(..., alias="invoiceReferenceNumber")
    ksef_reference_number: str = Field(..., alias="ksefReferenceNumber")
    invoice_hash: Optional[HashSHA] = Field(None, alias="invoiceHash")
    invoicing_date: date = Field(..., alias="invoicingDate")
    acquisition_timestamp: datetime = Field(..., alias="acquisitionTimestamp")
    subject_by: SubjectInfo = Field(..., alias="subjectBy")
    subject_to: Optional[SubjectInfo] = Field(None, alias="subjectTo")
    net: Decimal = Field(..., description="Net amount")
    vat: Decimal = Field(..., description="VAT amount")
    gross: Decimal = Field(..., description="Gross amount")
    currency: str = Field(default="PLN")
    schema_version: Optional[str] = Field(None, alias="schemaVersion")
    invoice_type: InvoiceType = Field(InvoiceType.VAT, alias="invoiceType")

    class Config:
        populate_by_name = True


class InvoiceListResponse(BaseModel):
    """Response containing list of invoices."""

    timestamp: datetime
    reference_number: str = Field(..., alias="referenceNumber")
    number_of_elements: int = Field(..., alias="numberOfElements")
    page_size: int = Field(..., alias="pageSize")
    page_offset: int = Field(..., alias="pageOffset")
    has_more: bool = Field(False, alias="hasMore")
    invoice_header_list: List[InvoiceHeader] = Field(
        default_factory=list, alias="invoiceHeaderList"
    )

    class Config:
        populate_by_name = True


class InvoiceQueryParams(BaseModel):
    """Query parameters for invoice search."""

    subject_type: SubjectType = Field(
        default=SubjectType.SUBJECT1,
        alias="subjectType",
        description="subject1=seller, subject2=buyer",
    )
    date_from: Optional[date] = Field(None, alias="dateFrom")
    date_to: Optional[date] = Field(None, alias="dateTo")
    acquisition_from: Optional[datetime] = Field(None, alias="acquisitionFrom")
    acquisition_to: Optional[datetime] = Field(None, alias="acquisitionTo")
    amount_from: Optional[Decimal] = Field(None, alias="amountFrom")
    amount_to: Optional[Decimal] = Field(None, alias="amountTo")
    invoice_type: Optional[InvoiceType] = Field(None, alias="invoiceType")
    nip_filter: Optional[str] = Field(None, alias="nipFilter")
    page_size: int = Field(default=50, ge=1, le=100, alias="pageSize")
    page_offset: int = Field(default=0, ge=0, alias="pageOffset")

    class Config:
        populate_by_name = True

    @field_validator("nip_filter")
    @classmethod
    def validate_nip_filter(cls, v: Optional[str]) -> Optional[str]:
        """Validate NIP filter if provided."""
        if v:
            v = v.strip().replace("-", "").replace(" ", "")
            if not v.isdigit():
                raise ValueError("NIP filter must contain only digits")
        return v


class InvoiceStatusResponse(BaseModel):
    """Response containing invoice status."""

    processing_code: int = Field(..., alias="processingCode")
    processing_description: Optional[str] = Field(None, alias="processingDescription")
    ksef_reference_number: Optional[str] = Field(None, alias="ksefReferenceNumber")
    timestamp: datetime
    acquisition_timestamp: Optional[datetime] = Field(None, alias="acquisitionTimestamp")
    upo_reference_number: Optional[str] = Field(None, alias="upoReferenceNumber")

    class Config:
        populate_by_name = True


class InvoiceDetail(BaseModel):
    """Detailed invoice information including XML content."""

    header: InvoiceHeader
    xml_content: Optional[str] = Field(None, alias="xmlContent")
    upo_available: bool = Field(False, alias="upoAvailable")
    cached_at: Optional[datetime] = Field(None, alias="cachedAt")

    class Config:
        populate_by_name = True


class InvoiceSyncRequest(BaseModel):
    """Request to sync invoices from KSeF."""

    subject_type: SubjectType = Field(
        default=SubjectType.SUBJECT1, alias="subjectType"
    )
    date_from: Optional[date] = Field(None, alias="dateFrom")
    date_to: Optional[date] = Field(None, alias="dateTo")
    full_sync: bool = Field(False, alias="fullSync", description="Clear cache first")

    class Config:
        populate_by_name = True


class InvoiceSyncResponse(BaseModel):
    """Response from invoice sync operation."""

    status: str = Field(..., description="sync status: started, completed, failed")
    total_fetched: int = Field(0, alias="totalFetched")
    new_invoices: int = Field(0, alias="newInvoices")
    updated_invoices: int = Field(0, alias="updatedInvoices")
    errors: List[str] = Field(default_factory=list)
    started_at: datetime = Field(..., alias="startedAt")
    completed_at: Optional[datetime] = Field(None, alias="completedAt")

    class Config:
        populate_by_name = True
