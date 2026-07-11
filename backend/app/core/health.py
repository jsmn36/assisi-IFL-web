"""Shared health-probe logic used by /health, /ready, and the
admin /api/v1/system-health endpoint.

A "component" check returns one of:
  - ``ok``      — required, passing
  - ``degraded`` — optional, passing with caveats
  - ``failed`` — required, failing → flips overall to ``unhealthy``

The overall status is the worst component status, but only ``failed``
required deps cause the readiness gate to 503.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict

from sqlalchemy import text

from app.core.cache import cache
from app.core.rate_limiter import rate_limiter
from app.database import SessionLocal, db_type

logger = logging.getLogger(__name__)


async def _check_database() -> Dict[str, Any]:
    """Required: a SELECT 1 must succeed."""
    def _probe() -> None:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
        finally:
            db.close()

    try:
        await asyncio.wait_for(asyncio.to_thread(_probe), timeout=2.0)
        return {"status": "ok", "type": db_type}
    except asyncio.TimeoutError:
        return {"status": "failed", "error": "timeout after 2s"}
    except Exception as exc:
        logger.exception("Database health probe failed")
        return {"status": "failed", "error": str(exc)[:200]}


async def _check_redis() -> Dict[str, Any]:
    """Optional: Redis is a soft dep (cache + rate limiting fall back)."""
    client = getattr(cache, "redis_client", None)
    if client is None:
        return {"status": "degraded", "message": "in-memory fallback"}
    try:
        ok = await asyncio.wait_for(asyncio.to_thread(client.ping), timeout=1.0)
        return {"status": "ok"} if ok else {"status": "degraded", "message": "ping returned falsey"}
    except Exception as exc:
        logger.warning("Redis health probe failed: %s", exc)
        return {"status": "degraded", "error": str(exc)[:200]}


async def _check_rate_limiter() -> Dict[str, Any]:
    """Optional: rate limiting requires Redis but is non-fatal."""
    if rate_limiter.redis_client is None:
        return {"status": "degraded", "message": "Redis unavailable — limits disabled"}
    try:
        await asyncio.wait_for(asyncio.to_thread(rate_limiter.redis_client.ping), timeout=1.0)
        return {"status": "ok"}
    except Exception as exc:
        return {"status": "degraded", "error": str(exc)[:200]}


async def _check_celery() -> Dict[str, Any]:
    """Optional: Celery only runs in PostgreSQL mode."""
    try:
        from app.config import settings

        if not settings.is_postgresql_mode:
            return {"status": "degraded", "message": "PostgreSQL mode disabled"}
        from app.core.celery_config import celery_app

        def _inspect() -> Dict[str, Any] | None:
            return celery_app.control.inspect(timeout=1).active()

        active = await asyncio.wait_for(asyncio.to_thread(_inspect), timeout=2.0)
        if active:
            return {"status": "ok", "workers": list(active.keys())}
        return {"status": "degraded", "message": "no active workers"}
    except Exception as exc:
        return {"status": "degraded", "error": str(exc)[:200]}


_CHECKS = {
    "database": (_check_database, True),
    "redis": (_check_redis, False),
    "rate_limiter": (_check_rate_limiter, False),
    "celery": (_check_celery, False),
}


async def collect_health() -> Dict[str, Any]:
    """Run every probe in parallel; return a single payload."""
    names, fns_required = zip(*[(n, fr) for n, fr in _CHECKS.items()])
    fns = [fr[0]() for fr in fns_required]
    results = await asyncio.gather(*fns, return_exceptions=True)

    components: Dict[str, Any] = {}
    overall = "ok"
    for name, (_, required), outcome in zip(names, fns_required, results):
        if isinstance(outcome, Exception):
            entry = {"status": "failed", "error": str(outcome)[:200]}
        else:
            entry = outcome  # type: ignore[assignment]
        components[name] = entry

        if entry["status"] == "failed" and required:
            overall = "unhealthy"
        elif entry["status"] == "degraded" and overall == "ok":
            overall = "degraded"

    return {"status": overall, "components": components}
