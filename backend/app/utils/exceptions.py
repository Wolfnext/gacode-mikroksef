"""Custom exception classes for KSeF operations."""

from typing import Optional


class KSeFError(Exception):
    """Base exception for KSeF-related errors."""

    def __init__(self, message: str, code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.code = code


class KSeFAPIError(KSeFError):
    """Exception for KSeF API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        code: Optional[str] = None,
    ):
        super().__init__(message, code)
        self.status_code = status_code


class KSeFAuthError(KSeFError):
    """Exception for authentication errors."""

    pass


class KSeFSessionError(KSeFError):
    """Exception for session-related errors."""

    pass


class KSeFRateLimitError(KSeFError):
    """Exception for rate limit errors."""

    def __init__(self, message: str, retry_after: int = 60):
        super().__init__(message)
        self.retry_after = retry_after


class KSeFValidationError(KSeFError):
    """Exception for validation errors."""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message)
        self.field = field
