"""Centralized structured logging.

One JSON line per log record with the contextvars (tenant_id, user_id,
request_id) folded into the payload. Idempotent — calling
``configure_logging`` more than once is safe (it replaces the root
handler in place).

The format is pure stdlib: no extra dep needed. Sentry/OpenTelemetry can
consume the same JSON via stderr collection without a parser plugin.
"""
from __future__ import annotations

import json
import logging
import logging.config
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict

from app.core.request_context import get_request_id, get_user_id
from app.core.tenant_context import get_tenant


# Standard fields the formatter always includes; everything else from the
# LogRecord (extras, exc_info) is folded under ``extra``.
_LOG_RECORD_BUILTINS = frozenset(
    {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "message",
        "taskName",
        "asctime",
    }
)


class JsonFormatter(logging.Formatter):
    """Render a LogRecord as a single-line JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        elif record.exc_text:
            payload["exc"] = record.exc_text

        # Fold context variables — these are the common-case correlation
        # keys used by audit/Sentry/log scrapers.
        try:
            payload["tenant_id"] = get_tenant()
        except Exception:
            payload["tenant_id"] = None
        try:
            payload["user_id"] = get_user_id()
        except Exception:
            payload["user_id"] = None
        try:
            payload["request_id"] = get_request_id()
        except Exception:
            payload["request_id"] = None

        # Anything passed via logger.info("msg", extra={...}) ends up as
        # plain attributes on the record. Bring those through.
        extras: Dict[str, Any] = {}
        for key, value in record.__dict__.items():
            if key in _LOG_RECORD_BUILTINS or key.startswith("_"):
                continue
            extras[key] = _safe_json(value)
        if extras:
            payload["extra"] = extras

        return json.dumps(payload, default=_safe_json)


def _safe_json(value: Any) -> Any:
    """Coerce values the JSON encoder can't handle into something it can."""
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return repr(value)


def configure_logging(level: str | None = None) -> None:
    """Install the JSON formatter on the root logger.

    Honors ``LOG_LEVEL`` env (default INFO). Forces our handler onto the
    root logger and removes any previously-installed ones so we don't
    double-log when an importer has already set up basicConfig.
    """
    log_level = (level or os.environ.get("LOG_LEVEL", "INFO")).upper()
    numeric_level = getattr(logging, log_level, logging.INFO)

    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setFormatter(JsonFormatter())
    handler.setLevel(numeric_level)

    root = logging.getLogger()
    for existing in list(root.handlers):
        root.removeHandler(existing)
    root.addHandler(handler)
    root.setLevel(numeric_level)

    # Tame the loudest libraries — keep their warnings, drop info-level
    # request/connection chatter that swamps real signal in dev.
    for noisy in ("uvicorn.access", "httpx", "httpcore", "urllib3", "asyncio"):
        logging.getLogger(noisy).setLevel(max(numeric_level, logging.WARNING))
