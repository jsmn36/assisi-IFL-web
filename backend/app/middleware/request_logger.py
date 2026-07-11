"""HTTP access logger.

Emits one structured record per request with method/path/status/duration
plus the contextvars (tenant, user, request_id) folded in by the JSON
formatter. Health/metrics paths are skipped to keep dashboards readable.
"""
import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("pms.access")

_QUIET_PATHS = ("/health", "/live", "/ready", "/metrics", "/favicon.ico")


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        skip_log = any(path.startswith(p) for p in _QUIET_PATHS)

        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "request_failed",
                extra={
                    "method": request.method,
                    "path": path,
                    "duration_ms": round(duration_ms, 2),
                    "client_ip": _client_ip(request),
                },
            )
            raise

        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

        if not skip_log:
            logger.info(
                "request",
                extra={
                    "method": request.method,
                    "path": path,
                    "status": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                    "client_ip": _client_ip(request),
                },
            )

        return response


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real = request.headers.get("X-Real-IP")
    if real:
        return real.strip()
    if request.client:
        return request.client.host
    return "unknown"
