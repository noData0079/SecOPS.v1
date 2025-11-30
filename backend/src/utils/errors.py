# backend/src/utils/errors.py

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class AppError(Exception):
    """
    Base application error with structured payload.

    Fields:
      - code: machine-readable error code (e.g. "auth.invalid_credentials")
      - message: human-readable message
      - http_status: HTTP status code to use when exposed via API
      - details: optional extra context (not always returned to clients)

    You can raise this anywhere in the core, services, or integrations.
    API layer can then convert it into HTTPException consistently.
    """

    def __init__(
        self,
        *,
        code: str,
        message: str,
        http_status: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.code = code
        self.message = message
        self.http_status = http_status
        self.details = details or {}
        super().__init__(message)

    def to_dict(self, include_details: bool = False) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "error": {
                "code": self.code,
                "message": self.message,
            }
        }
        if include_details and self.details:
            payload["error"]["details"] = self.details
        return payload

    def to_http_exception(self, include_details: bool = False) -> HTTPException:
        """
        Convert to FastAPI HTTPException with JSON body.
        """
        payload = self.to_dict(include_details=include_details)
        return HTTPException(
            status_code=self.http_status,
            detail=payload["error"],  # FastAPI will wrap this as {"detail": {...}}
        )


# ---------------------------------------------------------------------------
# Common subclasses
# ---------------------------------------------------------------------------


class NotFoundError(AppError):
    def __init__(
        self,
        *,
        message: str = "Resource not found",
        code: str = "common.not_found",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            code=code,
            message=message,
            http_status=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class ValidationError(AppError):
    def __init__(
        self,
        *,
        message: str = "Validation failed",
        code: str = "common.validation_error",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            code=code,
            message=message,
            http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class AuthError(AppError):
    def __init__(
        self,
        *,
        message: str = "Authentication failed",
        code: str = "auth.failed",
        http_status: int = status.HTTP_401_UNAUTHORIZED,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            code=code,
            message=message,
            http_status=http_status,
            details=details,
        )


class PermissionDeniedError(AppError):
    def __init__(
        self,
        *,
        message: str = "You do not have permission to perform this action",
        code: str = "auth.permission_denied",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            code=code,
            message=message,
            http_status=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class ConflictError(AppError):
    def __init__(
        self,
        *,
        message: str = "Resource conflict",
        code: str = "common.conflict",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            code=code,
            message=message,
            http_status=status.HTTP_409_CONFLICT,
            details=details,
        )


# ---------------------------------------------------------------------------
# Helper for API layer
# ---------------------------------------------------------------------------


def handle_app_error(err: AppError, *, include_details: bool = False) -> HTTPException:
    """
    Convert an AppError into HTTPException and log it.

    Usage in route handlers:

        from utils.errors import AppError, handle_app_error

        @router.get("/something")
        async def endpoint():
            try:
                ...
            except AppError as e:
                raise handle_app_error(e)

    """
    # You can customize logging level per type if you like
    logger.warning(
        "AppError raised: code=%s message=%s details=%s",
        err.code,
        err.message,
        err.details,
    )
    return err.to_http_exception(include_details=include_details)


def unexpected_error_to_http(exc: Exception) -> HTTPException:
    """
    Fallback converter for unexpected exceptions.

    Use this if you want a consistent JSON error even on unhandled errors,
    but typically you'll rely on FastAPI's default handlers and let your
    logging capture the stack trace.
    """
    logger.exception("Unexpected error: %s", exc)
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={
            "code": "common.internal_error",
            "message": "Internal server error",
        },
    )
