# backend/src/utils/errors.py

"""Custom exception classes for The Sovereign Mechanica (TSM99)."""

from fastapi import HTTPException
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR


class T79Error(HTTPException):
    """Base error for TSM99 Platform (formerly T79)."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(status_code=status_code, detail=message)


# Aliases for compatibility and new branding
SecOpsError = T79Error
TSM99Error = T79Error


class IntegrationError(T79Error):
    """Raised when an external integration fails."""
    def __init__(self, message: str = "Integration error occurred", status_code: int = 502):
        super().__init__(message, status_code)


class LLMError(T79Error):
    """Raised when an LLM operation fails."""
    def __init__(self, message: str = "LLM request failed", status_code: int = 503):
        super().__init__(message, status_code)


class AnalyzerError(T79Error):
    """Raised when analysis/scanning fails."""
    def __init__(self, message: str = "Analysis failed", status_code: int = 500):
        super().__init__(message, status_code)


class ValidationError(T79Error):
    """Raised when validation fails."""
    def __init__(self, message: str = "Validation failed", status_code: int = 422):
        super().__init__(message, status_code)


class AuthenticationError(T79Error):
    """Raised when authentication fails."""
    def __init__(self, message: str = "Authentication failed", status_code: int = 401):
        super().__init__(message, status_code)


class AuthorizationError(T79Error):
    """Raised when authorization fails."""
    def __init__(self, message: str = "Access denied", status_code: int = 403):
        super().__init__(message, status_code)


def internal_error(message: str = "Internal server error"):
    raise HTTPException(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        detail=message
    )
