from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Optional
from app.core.rate_limiter import rate_limiter
from app.core.rate_limit_config import RateLimitConfig


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware

    Applies multiple layers of rate limiting:
    1. IP-based (default limits)
    2. User-based (if authenticated)
    3. Endpoint-specific (if configured)
    """

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/api/v1/monitoring/health"]:
            return await call_next(request)

        # Get client IP
        client_ip = self._get_client_ip(request)

        # Get user info safely
        user = getattr(request.state, "user", None)
        user_id: Optional[str] = getattr(user, "id", None)
        user_role: Optional[str] = getattr(user, "role", None)

        checks = []

        # 1. IP-based rate limit
        ip_key = f"ip:{client_ip}"
        ip_limit, ip_window = RateLimitConfig.DEFAULT_LIMITS["per_minute"]

        checks.append((ip_key, ip_limit, ip_window))

        # 2. User-based rate limit
        if user_id:
            tier = RateLimitConfig.get_user_tier(user_role)
            user_limits = RateLimitConfig.USER_LIMITS[tier]

            user_key = f"user:{user_id}"
            user_limit, user_window = user_limits["per_minute"]

            checks.append((user_key, user_limit, user_window))

        # 3. Endpoint-specific rate limit
        endpoint_limit = RateLimitConfig.get_endpoint_limit(
            request.url.path, request.method
        )

        if endpoint_limit:
            endpoint_key = f"endpoint:{client_ip}:{request.url.path}"
            checks.append((endpoint_key, endpoint_limit[0], endpoint_limit[1]))

        # Execute rate limit checks
        allowed, info = rate_limiter.check_multiple_limits(checks)

        if allowed:
            response = await call_next(request)
            self._add_rate_limit_headers(response, info)
            return response

        rate_limiter.record_violation(
            key=info.get("key") or ip_key,
            limit=info.get("limit", 0),
            window_seconds=info.get("window", 60),
            ip=client_ip,
            path=request.url.path,
            user_id=user_id,
        )
        return self._create_rate_limit_response(info)

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address safely"""

        # X-Forwarded-For can contain multiple IPs → take first
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # X-Real-IP
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # Direct connection fallback
        if request.client:
            return request.client.host

        return "unknown"

    def _add_rate_limit_headers(self, response: Response, info: dict):
        """Attach rate limit headers"""

        response.headers["X-RateLimit-Limit"] = str(info.get("limit", 0))
        response.headers["X-RateLimit-Remaining"] = str(info.get("remaining", 0))
        response.headers["X-RateLimit-Reset"] = str(info.get("reset", 0))

        if "retry_after" in info:
            response.headers["Retry-After"] = str(info["retry_after"])

    def _create_rate_limit_response(self, info: dict) -> JSONResponse:
        """Return 429 response"""

        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "rate_limit_exceeded",
                "message": "Too many requests. Please try again later.",
                "limit": info.get("limit", 0),
                "remaining": info.get("remaining", 0),
                "reset": info.get("reset", 0),
                "retry_after": info.get("retry_after"),
            },
            headers={
                "X-RateLimit-Limit": str(info.get("limit", 0)),
                "X-RateLimit-Remaining": str(info.get("remaining", 0)),
                "X-RateLimit-Reset": str(info.get("reset", 0)),
                "Retry-After": str(info.get("retry_after", 60)),
            },
        )
