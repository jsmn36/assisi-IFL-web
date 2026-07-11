"""
API Error Handlers
Centralized error handling for API
"""
import logging
import uuid

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.services.base_service import (
    ServiceError,
    ValidationError,
    NotFoundError,
    BusinessRuleError,
)

logger = logging.getLogger(__name__)


async def service_error_handler(request: Request, exc: ServiceError):
    """Handle service errors"""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    if isinstance(exc, ValidationError):
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, NotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, BusinessRuleError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": exc.message,
            "code": exc.code,
            "details": exc.details,
        },
    )


def _scrub_for_json(value):
    """Recursively coerce non-JSON-serializable bits (bytes, etc.) to str.

    FastAPI's RequestValidationError.errors() may include raw request body
    bytes in the ``input`` field when JSON parsing fails. Those bytes blow up
    JSONResponse.render. Walk and replace.
    """
    if isinstance(value, dict):
        return {k: _scrub_for_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_scrub_for_json(v) for v in value]
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8", errors="replace")
        except Exception:
            return repr(value)
    return value


async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Validation error",
            "code": "VALIDATION_ERROR",
            "details": _scrub_for_json(exc.errors()),
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    """Catch-all for unhandled exceptions.

    Logs with a request_id and returns a stable JSON envelope. In non-prod the
    exception class + message are echoed back to aid debugging; in prod only
    the request_id is returned so the user can cross-reference logs.
    """
    request_id = getattr(request.state, "request_id", None) or uuid.uuid4().hex
    logger.exception(
        "Unhandled exception on %s %s (request_id=%s)",
        request.method,
        request.url.path,
        request_id,
    )

    body = {
        "success": False,
        "error": "Internal server error",
        "code": "INTERNAL_ERROR",
        "request_id": request_id,
    }
    if not settings.is_production:
        body["exception"] = f"{exc.__class__.__name__}: {exc}"

    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=body)
