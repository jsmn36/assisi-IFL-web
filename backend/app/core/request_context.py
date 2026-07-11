"""Per-request context shared across logging, audit, and error reporting.

Holds a request id (correlation id) plus a copy of the authenticated user
id when available. Tenant id lives separately in
:mod:`app.core.tenant_context` and is read by callers that need it.
"""
from __future__ import annotations

import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator, Optional

_request_id: ContextVar[Optional[str]] = ContextVar(
    "pms_request_id", default=None
)
_user_id: ContextVar[Optional[int]] = ContextVar(
    "pms_user_id", default=None
)


def new_request_id() -> str:
    """Return a fresh hex request id."""
    return uuid.uuid4().hex


def set_request_id(value: Optional[str]):
    return _request_id.set(value)


def get_request_id() -> Optional[str]:
    return _request_id.get()


def set_user_id(value: Optional[int]):
    return _user_id.set(value)


def get_user_id() -> Optional[int]:
    return _user_id.get()


@contextmanager
def request_scope(request_id: Optional[str] = None) -> Iterator[str]:
    """Convenience wrapper for tests/scripts that want a clean request scope."""
    rid = request_id or new_request_id()
    token = _request_id.set(rid)
    try:
        yield rid
    finally:
        _request_id.reset(token)
