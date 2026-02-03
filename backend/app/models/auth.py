"""Authentication-related Pydantic models."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class IdentifierType(str, Enum):
    """Type of subject identifier."""

    NIP = "onip"
    PESEL = "pesel"
    OTHER = "other"


class SubjectIdentifier(BaseModel):
    """Subject identifier (NIP, PESEL, etc.)."""

    type: IdentifierType = Field(..., description="Identifier type")
    identifier: str = Field(..., description="Identifier value")

    @field_validator("identifier")
    @classmethod
    def validate_identifier(cls, v: str, info) -> str:
        """Validate identifier format based on type."""
        v = v.strip().replace("-", "").replace(" ", "")
        if info.data.get("type") == IdentifierType.NIP and len(v) != 10:
            raise ValueError("NIP must be 10 digits")
        if info.data.get("type") == IdentifierType.PESEL and len(v) != 11:
            raise ValueError("PESEL must be 11 digits")
        return v


class AuthChallengeRequest(BaseModel):
    """Request for authorization challenge."""

    context_identifier: SubjectIdentifier = Field(
        ...,
        alias="contextIdentifier",
        description="Subject identifier for authentication context",
    )

    class Config:
        populate_by_name = True


class AuthChallengeResponse(BaseModel):
    """Response containing authorization challenge."""

    timestamp: datetime = Field(..., description="Server timestamp")
    challenge: str = Field(..., description="Challenge string to sign")


class InitTokenRequest(BaseModel):
    """Request to initialize session with token."""

    nip: str = Field(
        ...,
        min_length=10,
        max_length=10,
        description="Company NIP (10 digits)",
    )

    @field_validator("nip")
    @classmethod
    def validate_nip(cls, v: str) -> str:
        """Validate and normalize NIP."""
        v = v.strip().replace("-", "").replace(" ", "")
        if not v.isdigit() or len(v) != 10:
            raise ValueError("NIP must be exactly 10 digits")
        return v


class SessionResponse(BaseModel):
    """Response containing session information."""

    session_token: str = Field(..., alias="sessionToken", description="Bearer token")
    reference_number: str = Field(
        ..., alias="referenceNumber", description="Session reference"
    )
    timestamp: datetime = Field(..., description="Session creation time")

    class Config:
        populate_by_name = True


class SessionStatusResponse(BaseModel):
    """Response containing session status."""

    reference_number: str = Field(..., alias="referenceNumber")
    processing_code: int = Field(..., alias="processingCode")
    processing_description: str = Field("", alias="processingDescription")
    number_of_elements: int = Field(0, alias="numberOfElements")
    timestamp: datetime
    is_active: bool = Field(True, alias="isActive")

    class Config:
        populate_by_name = True


class CredentialsInfo(BaseModel):
    """Information about stored credentials."""

    nip: str
    has_token: bool = Field(..., alias="hasToken")
    has_certificate: bool = Field(..., alias="hasCertificate")
    token_expires_at: Optional[datetime] = Field(None, alias="tokenExpiresAt")

    class Config:
        populate_by_name = True
