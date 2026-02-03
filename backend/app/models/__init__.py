"""Pydantic models for request/response validation."""

from app.models.auth import (
    IdentifierType,
    SubjectIdentifier,
    AuthChallengeRequest,
    AuthChallengeResponse,
    InitTokenRequest,
    SessionResponse,
    SessionStatusResponse,
)
from app.models.invoice import (
    InvoiceType,
    SubjectType,
    HashSHA,
    SubjectInfo,
    InvoiceHeader,
    InvoiceListResponse,
    InvoiceQueryParams,
    InvoiceStatusResponse,
    InvoiceDetail,
    InvoiceSyncRequest,
    InvoiceSyncResponse,
)
from app.models.common import (
    ErrorResponse,
    ErrorDetail,
    PaginationParams,
    HealthResponse,
)

__all__ = [
    # Auth
    "IdentifierType",
    "SubjectIdentifier",
    "AuthChallengeRequest",
    "AuthChallengeResponse",
    "InitTokenRequest",
    "SessionResponse",
    "SessionStatusResponse",
    # Invoice
    "InvoiceType",
    "SubjectType",
    "HashSHA",
    "SubjectInfo",
    "InvoiceHeader",
    "InvoiceListResponse",
    "InvoiceQueryParams",
    "InvoiceStatusResponse",
    "InvoiceDetail",
    "InvoiceSyncRequest",
    "InvoiceSyncResponse",
    # Common
    "ErrorResponse",
    "ErrorDetail",
    "PaginationParams",
    "HealthResponse",
]
