"""Tenant-resolution middleware.

Resolves the tenant id for the current request and installs it on the
request-scoped contextvar read by the SQLAlchemy session filter.

Resolution order:
1. Explicit ``X-Impersonate-Tenant`` header when the caller is a superadmin
   (claim ``is_superadmin: true`` in their JWT).
2. Internal service token: calls authenticated with the
   ``INTERNAL_SERVICE_TOKEN`` must supply ``X-Tenant-Id`` and get no
   isolation bypass — just that tenant.
3. ``tenant_id`` claim on the user's JWT.

Paths on the whitelist (health, docs, login, refresh, CM webhooks) skip
resolution entirely and run without a tenant set.
"""
from __future__ import annotations

import logging
from typing import Callable, Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.core.security import verify_token
from app.core.tenant_context import set_tenant, reset_tenant

logger = logging.getLogger(__name__)


WHITELIST_PREFIXES = (
    "/health",
    "/live",
    "/ready",
    "/metrics",
    "/favicon.ico",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
    "/api/v1/auth/select-tenant",
    "/api/v1/auth/me",
    "/api/v1/auth/memberships",
    # Channel-manager ingress webhooks carry their own HMAC, not a JWT.
    "/api/v1/cm/webhooks",
    # Payment provider webhooks carry their own signature; the handler
    # resolves the tenant from the PaymentIntent metadata.
    "/api/v1/payments/webhooks/",
    "/database/info",
    "/",
)


def _extract_bearer(request: Request) -> Optional[str]:
    # Cookie first (matches get_current_user precedence)
    token = request.cookies.get("access_token")
    if token:
        return token
    auth = request.headers.get("Authorization") or request.headers.get("authorization")
    if not auth:
        return None
    scheme, _, credentials = auth.partition(" ")
    if scheme.lower() != "bearer" or not credentials:
        return None
    return credentials


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        if any(path.startswith(prefix) for prefix in WHITELIST_PREFIXES):
            return await call_next(request)

        tenant_id = self._resolve_tenant(request)

        if tenant_id is None:
            # Downstream auth will 401 — but for clarity respond now for
            # endpoints that would be tenant-scoped anyway.
            return await call_next(request)

        token = set_tenant(tenant_id)
        try:
            request.state.tenant_id = tenant_id
            return await call_next(request)
        finally:
            reset_tenant(token)

    def _resolve_tenant(self, request: Request) -> Optional[int]:
        # Internal service token path
        service_token = request.headers.get("X-Service-Token")
        if (
            service_token
            and settings.INTERNAL_SERVICE_TOKEN
            and service_token == settings.INTERNAL_SERVICE_TOKEN
        ):
            hdr = request.headers.get("X-Tenant-Id")
            if hdr and hdr.isdigit():
                return int(hdr)
            logger.warning(
                "Service-token request to %s missing/invalid X-Tenant-Id header",
                request.url.path,
            )
            return None

        bearer = _extract_bearer(request)
        if not bearer:
            return None

        payload = verify_token(bearer)
        if payload is None:
            return None

        # Superadmin impersonation
        if payload.get("is_superadmin") is True:
            impersonate = request.headers.get("X-Impersonate-Tenant")
            if impersonate and impersonate.isdigit():
                return int(impersonate)

        tenant_claim = payload.get("tenant_id")
        if isinstance(tenant_claim, int):
            return tenant_claim
        if isinstance(tenant_claim, str) and tenant_claim.isdigit():
            return int(tenant_claim)
        return None
