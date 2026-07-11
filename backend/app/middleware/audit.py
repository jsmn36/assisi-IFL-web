"""
Audit Middleware
Writes an AuditLog row for mutating HTTP requests.
Read-only traffic (GET/HEAD/OPTIONS) is not logged to keep write amplification bounded.
"""
import logging
from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.database import SessionLocal
from app.services.audit_helper import write_audit

logger = logging.getLogger(__name__)

MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

SKIP_PATH_PREFIXES = (
    "/health",
    "/metrics",
    "/favicon.ico",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
)


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        if request.method not in MUTATING_METHODS:
            return response

        path = request.url.path
        if any(path.startswith(prefix) for prefix in SKIP_PATH_PREFIXES):
            return response

        user = getattr(request.state, "user", None)
        status_label = "success" if 200 <= response.status_code < 400 else "failure"

        self._write_audit_safe(
            action=f"{request.method} {path}",
            resource_type=self._resource_from_path(path),
            user=user,
            status_label=status_label,
            ip_address=self._client_ip(request),
            details=f"status_code={response.status_code}",
        )
        return response

    @staticmethod
    def _resource_from_path(path: str) -> str:
        parts = [p for p in path.split("/") if p]
        if len(parts) >= 3 and parts[0] == "api":
            return parts[2]
        return parts[0] if parts else "unknown"

    @staticmethod
    def _client_ip(request: Request) -> Optional[str]:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        if request.client:
            return request.client.host
        return None

    @staticmethod
    def _write_audit_safe(
        *,
        action: str,
        resource_type: str,
        user,
        status_label: str,
        ip_address: Optional[str],
        details: Optional[str],
    ) -> None:
        db = SessionLocal()
        try:
            write_audit(
                db,
                action=action,
                resource_type=resource_type,
                current_user=user,
                status=status_label,
                ip_address=ip_address,
                details=details,
            )
        except Exception:
            logger.exception("Failed to write audit log for %s", action)
            try:
                db.rollback()
            except Exception:
                logger.debug("Audit rollback also failed", exc_info=True)
        finally:
            db.close()
