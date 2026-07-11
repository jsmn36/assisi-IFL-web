"""Request-ID middleware.

Reads ``X-Request-ID`` if the caller supplied one (gateway-issued ids let
us correlate across services), otherwise generates one. The id is:

  1. installed in the contextvar so every log line and audit row inherits it,
  2. attached to ``request.state.request_id`` for handlers that want it,
  3. echoed on the response as ``X-Request-ID``.

Should be the OUTERMOST middleware so even rate-limit rejections carry an id.
"""
from __future__ import annotations

from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.request_context import (
    new_request_id,
    set_request_id,
    set_user_id,
    _request_id,
    _user_id,
)


_INCOMING_HEADER = "x-request-id"


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        incoming = request.headers.get(_INCOMING_HEADER)
        # Only honor reasonably-shaped incoming ids — defensive, since the
        # value goes into log lines and downstream service hops.
        if incoming and 8 <= len(incoming) <= 128 and all(
            c.isalnum() or c in "-_" for c in incoming
        ):
            request_id = incoming
        else:
            request_id = new_request_id()

        rid_token = set_request_id(request_id)
        uid_token = set_user_id(None)
        request.state.request_id = request_id
        try:
            response = await call_next(request)
        finally:
            _request_id.reset(rid_token)
            _user_id.reset(uid_token)

        response.headers["X-Request-ID"] = request_id
        return response
