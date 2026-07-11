"""Optional Sentry initialization.

Active only when ``SENTRY_DSN`` is set in the environment. The package
``sentry-sdk[fastapi]`` is a soft dependency — if it's not installed
(e.g. on a minimal dev box) we log a single warning and skip.

A ``before_send`` hook tags every event with the current tenant/user/
request id from contextvars so dashboards can be filtered by tenant.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

from app.core.request_context import get_request_id, get_user_id
from app.core.tenant_context import get_tenant

logger = logging.getLogger(__name__)


def _annotate(event: Dict[str, Any], hint: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Sentry ``before_send`` hook: fold context into tags."""
    tags = event.setdefault("tags", {})
    try:
        tenant_id = get_tenant()
        if tenant_id is not None:
            tags["tenant_id"] = tenant_id
    except Exception:
        pass
    try:
        user_id = get_user_id()
        if user_id is not None:
            tags["user_id"] = user_id
            event.setdefault("user", {}).setdefault("id", user_id)
    except Exception:
        pass
    try:
        request_id = get_request_id()
        if request_id is not None:
            tags["request_id"] = request_id
    except Exception:
        pass
    return event


def init_observability() -> None:
    """Initialize Sentry if SENTRY_DSN is set; no-op otherwise."""
    dsn = os.environ.get("SENTRY_DSN", "").strip()
    if not dsn:
        return

    try:
        import sentry_sdk  # type: ignore[import-not-found]
        from sentry_sdk.integrations.fastapi import FastApiIntegration  # type: ignore[import-not-found]
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration  # type: ignore[import-not-found]
        from sentry_sdk.integrations.celery import CeleryIntegration  # type: ignore[import-not-found]
    except Exception as exc:
        logger.warning(
            "SENTRY_DSN is set but sentry-sdk is not importable; skipping init: %s", exc
        )
        return

    environment = os.environ.get("APP_ENV", "development")
    release = os.environ.get("SENTRY_RELEASE")
    sample_rate = float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1"))

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        release=release,
        traces_sample_rate=sample_rate,
        send_default_pii=False,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
            CeleryIntegration(),
        ],
        before_send=_annotate,
        before_send_transaction=_annotate,
    )
    logger.info("Sentry initialized (env=%s, sample=%s)", environment, sample_rate)
