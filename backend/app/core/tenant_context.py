"""Request-scoped tenant context.

The value is populated by :mod:`app.middleware.tenant` from the JWT
``tenant_id`` claim (or by service-token handlers) and read by the
SQLAlchemy session filter registered in :mod:`app.database`.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator, Optional

_current_tenant: ContextVar[Optional[int]] = ContextVar(
    "pms_current_tenant_id", default=None
)

# When True, tenant isolation filtering is bypassed for the current context.
# Used by the superadmin impersonation path, cross-tenant migrations, and
# unit-test fixtures. NEVER set this from a regular request handler.
_bypass_flag: ContextVar[bool] = ContextVar("pms_tenant_bypass", default=False)


def set_tenant(tenant_id: Optional[int]):
    """Install ``tenant_id`` for the current task. Returns the reset token."""
    return _current_tenant.set(tenant_id)


def reset_tenant(token) -> None:
    """Undo a previous :func:`set_tenant` using the returned token."""
    _current_tenant.reset(token)


def get_tenant() -> Optional[int]:
    """Return the tenant id installed for the current task, or None."""
    return _current_tenant.get()


def require_tenant() -> int:
    """Return the current tenant id; raise if none is set."""
    tid = _current_tenant.get()
    if tid is None:
        raise RuntimeError(
            "No tenant context is set. This operation requires a tenant-bound request."
        )
    return tid


def is_bypassing() -> bool:
    """Return True when tenant isolation is temporarily disabled."""
    return _bypass_flag.get()


@contextmanager
def tenant_scope(tenant_id: Optional[int]) -> Iterator[None]:
    """Context manager that sets and reliably clears the tenant id."""
    token = _current_tenant.set(tenant_id)
    try:
        yield
    finally:
        _current_tenant.reset(token)


@contextmanager
def bypass_tenant_filter() -> Iterator[None]:
    """Context manager that temporarily disables the tenant filter.

    Intended for migrations, superadmin tooling, and tenant-loop schedulers
    that intentionally iterate every tenant.
    """
    token = _bypass_flag.set(True)
    try:
        yield
    finally:
        _bypass_flag.reset(token)
