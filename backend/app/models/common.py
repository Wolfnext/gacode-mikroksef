"""Common/shared Pydantic models."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Detailed error information."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    field: Optional[str] = Field(None, description="Field that caused the error")


class ErrorResponse(BaseModel):
    """Standard error response format."""

    detail: str = Field(..., description="Error summary")
    type: str = Field(default="error", description="Error type")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Error timestamp"
    )
    errors: List[ErrorDetail] = Field(
        default_factory=list, description="Detailed errors"
    )
    reference: Optional[str] = Field(None, description="Error reference for support")


class PaginationParams(BaseModel):
    """Pagination parameters."""

    page_size: int = Field(default=50, ge=1, le=100, alias="pageSize")
    page_offset: int = Field(default=0, ge=0, alias="pageOffset")

    class Config:
        populate_by_name = True

    @property
    def skip(self) -> int:
        """Calculate skip value for database queries."""
        return self.page_offset

    @property
    def limit(self) -> int:
        """Get limit value for database queries."""
        return self.page_size


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    environment: str = Field(..., description="KSeF environment")
    ksef_api: str = Field(..., alias="ksefApi", description="KSeF API URL")
    session_active: bool = Field(..., alias="sessionActive")
    session_reference: Optional[str] = Field(None, alias="sessionReference")
    database_connected: bool = Field(True, alias="databaseConnected")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(default="1.0.0")

    class Config:
        populate_by_name = True
