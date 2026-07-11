"""
Cache Middleware
HTTP response caching for GET endpoints
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import hashlib
from app.core.cache import cache


class CacheMiddleware(BaseHTTPMiddleware):
    CACHE_ROUTES = [
        ("GET", "/api/v1/dashboard/stats", 60),
        ("GET", "/api/v1/rooms/availability", 300),
    ]

    SKIP_ROUTES = [
        "/api/v1/auth/",
        "/api/v1/payments/",
        "/api/v1/audit/",
    ]

    STRIP_HEADERS = {"content-encoding", "transfer-encoding", "content-length"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.method != "GET":
            return await call_next(request)

        path = request.url.path
        if any(skip in path for skip in self.SKIP_ROUTES):
            return await call_next(request)

        cache_ttl = self._get_cache_ttl(path)
        if not cache_ttl:
            return await call_next(request)

        cache_key = self._generate_cache_key(request)
        cached = cache.get(cache_key)
        if cached:
            return Response(
                content=cached["body"],
                status_code=cached["status_code"],
                headers=cached["headers"],
                media_type=cached["media_type"],
            )

        response = await call_next(request)

        if response.status_code == 200:
            body = b""
            async for chunk in response.body_iterator:
                body += chunk

            safe_headers = {
                k: v
                for k, v in response.headers.items()
                if k.lower() not in self.STRIP_HEADERS
            }

            cache.set(
                cache_key,
                {
                    "body": body,
                    "status_code": response.status_code,
                    "headers": safe_headers,
                    "media_type": response.media_type,
                },
                ttl=cache_ttl,
            )

            return Response(
                content=body,
                status_code=response.status_code,
                headers=safe_headers,
                media_type=response.media_type,
            )

        return response

    def _get_cache_ttl(self, path: str) -> int:
        for _method, cached_path, ttl in self.CACHE_ROUTES:
            if path.startswith(cached_path):
                return ttl
        return 0

    def _generate_cache_key(self, request: Request) -> str:
        user_id = "anonymous"
        if hasattr(request.state, "user") and request.state.user:
            user_id = str(request.state.user.id)
        key_string = ":".join(
            [
                request.method,
                request.url.path,
                str(sorted(request.query_params.items())),
                user_id,
            ]
        )
        return hashlib.md5(key_string.encode()).hexdigest()
