"""Custom exceptions for the Wago WhatsApp API client."""

from __future__ import annotations

from typing import Any, Optional


class WagoError(Exception):
    """Base exception for all Wago client errors."""

    def __init__(self, message: str, code: Optional[str] = None, status: Optional[int] = None, details: Any = None):
        self.message = message
        self.code = code
        self.status = status
        self.details = details
        super().__init__(message)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, code={self.code!r}, status={self.status})"


class WagoBadRequestError(WagoError):
    """Raised when the server returns a 400 Bad Request."""
    pass


class WagoUnauthorizedError(WagoError):
    """Raised when the server returns a 401 Unauthorized."""
    pass


class WagoNotFoundError(WagoError):
    """Raised when the server returns a 404 Not Found."""
    pass


class WagoConflictError(WagoError):
    """Raised when the server returns a 409 Conflict."""
    pass


class WagoInternalServerError(WagoError):
    """Raised when the server returns a 500 Internal Server Error."""
    pass


class WagoConnectionError(WagoError):
    """Raised when the client cannot connect to the server."""
    pass
