"""Helpers for running periodic jobs across every active tenant.

Background jobs (CRM sync, analytics aggregation, night-audit, retention
sweeps) operate on tenant-scoped data, but they aren't triggered by a
specific HTTP request, so no tenant claim is in scope. This helper runs
the supplied callable once per active tenant with the tenant context
correctly installed for each iteration.

Usage:
    from app.core.tenant_loop import run_for_each_tenant

    def my_job():
        # SQLAlchemy queries here will be auto-filtered to the current tenant
        ...

    run_for_each_tenant(my_job)
"""
from __future__ import annotations

import logging
from typing import Callable, Iterable, List, Optional

from app.core.tenant_context import bypass_tenant_filter, tenant_scope
from app.database import SessionLocal

logger = logging.getLogger(__name__)


def get_active_tenant_ids() -> List[int]:
    """Return ids of all active tenants (uses bypass to read across all)."""
    from app.models import Tenant

    db = SessionLocal()
    try:
        with bypass_tenant_filter():
            rows = db.query(Tenant.id).filter(Tenant.is_active == True).all()  # noqa: E712
        return [r[0] for r in rows]
    finally:
        db.close()


def run_for_each_tenant(
    fn: Callable[[], None],
    *,
    tenant_ids: Optional[Iterable[int]] = None,
    job_name: Optional[str] = None,
    raise_on_error: bool = False,
) -> dict:
    """Invoke ``fn`` once per tenant id, with the tenant context set.

    Returns a per-tenant dict of "ok" / "error: ..." for observability.
    """
    name = job_name or fn.__name__
    ids = list(tenant_ids) if tenant_ids is not None else get_active_tenant_ids()
    results: dict = {}
    for tid in ids:
        with tenant_scope(tid):
            try:
                fn()
                results[tid] = "ok"
            except Exception:
                logger.exception("Tenant-loop job %s failed for tenant_id=%s", name, tid)
                results[tid] = "error"
                if raise_on_error:
                    raise
    logger.info("Tenant-loop job %s completed across %d tenants", name, len(ids))
    return results
