"""py-wago — Async Python client for the Wago WhatsApp API."""

from .client import WagoClient
from .exceptions import (
    WagoBadRequestError,
    WagoConflictError,
    WagoConnectionError,
    WagoError,
    WagoInternalServerError,
    WagoNotFoundError,
    WagoUnauthorizedError,
)

__all__ = [
    "WagoClient",
    "WagoBadRequestError",
    "WagoConflictError",
    "WagoConnectionError",
    "WagoError",
    "WagoInternalServerError",
    "WagoNotFoundError",
    "WagoUnauthorizedError",
]

__version__ = "0.1.0"
