"""SMS provider abstraction.

Twilio is the reference implementation. The same shape works for
MessageBird/AWS SNS — implement :class:`SMSProvider` and return it from
:func:`get_default_sms_provider`.

All env vars are optional; if Twilio creds are missing the provider
short-circuits to a :class:`NoOpSMSProvider` that logs and returns a
synthetic id. That keeps dev environments runnable without setting up
Twilio.
"""
from __future__ import annotations

import logging
import os
import uuid
from dataclasses import dataclass
from typing import Optional, Protocol

logger = logging.getLogger(__name__)


class SMSProviderError(Exception):
    """SDK-level errors mapped to a single exception type."""


@dataclass
class SMSResult:
    provider: str
    provider_message_id: str
    status: str  # "queued" | "sent" | "delivered" | "failed"
    to: str
    error: Optional[str] = None


class SMSProvider(Protocol):
    name: str

    def send(self, *, to: str, body: str, sender: Optional[str] = None) -> SMSResult:
        ...


# ─── Twilio ───────────────────────────────────────────────────────────────
class TwilioSMSProvider:
    name = "twilio"

    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        from_number: str,
    ) -> None:
        if not account_sid or not auth_token or not from_number:
            raise SMSProviderError(
                "Twilio requires TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN and TWILIO_FROM_NUMBER"
            )
        try:
            from twilio.rest import Client  # type: ignore[import-not-found]
        except ImportError as exc:
            raise SMSProviderError(
                "twilio SDK not installed. Add `twilio>=8.0.0` to requirements.txt."
            ) from exc
        self._client = Client(account_sid, auth_token)
        self._from_number = from_number

    def send(self, *, to: str, body: str, sender: Optional[str] = None) -> SMSResult:
        try:
            msg = self._client.messages.create(
                to=to,
                from_=sender or self._from_number,
                body=body[:1600],  # Twilio segments above this; cap defensively.
            )
        except Exception as exc:
            logger.exception("Twilio send failed to=%s", to)
            return SMSResult(
                provider=self.name,
                provider_message_id="",
                status="failed",
                to=to,
                error=str(exc)[:500],
            )
        return SMSResult(
            provider=self.name,
            provider_message_id=msg.sid,
            status=getattr(msg, "status", "queued") or "queued",
            to=to,
        )


# ─── No-op fallback ───────────────────────────────────────────────────────
class NoOpSMSProvider:
    """Used when no SMS credentials are configured.

    Logs the message at INFO and returns a synthetic id so callers don't
    have to special-case dev environments.
    """

    name = "noop"

    def send(self, *, to: str, body: str, sender: Optional[str] = None) -> SMSResult:
        message_id = f"noop_{uuid.uuid4().hex[:12]}"
        logger.info(
            "SMS noop send",
            extra={
                "to": to,
                "sender": sender,
                "body_preview": body[:120],
                "provider_message_id": message_id,
            },
        )
        return SMSResult(
            provider=self.name,
            provider_message_id=message_id,
            status="sent",
            to=to,
        )


_default_provider: Optional[SMSProvider] = None


def get_default_sms_provider() -> SMSProvider:
    """Return the process-wide SMS provider, configured from env."""
    global _default_provider
    if _default_provider is not None:
        return _default_provider

    sid = os.environ.get("TWILIO_ACCOUNT_SID", "").strip()
    token = os.environ.get("TWILIO_AUTH_TOKEN", "").strip()
    from_number = os.environ.get("TWILIO_FROM_NUMBER", "").strip()

    if sid and token and from_number:
        try:
            _default_provider = TwilioSMSProvider(sid, token, from_number)
            logger.info("SMS provider: Twilio configured")
            return _default_provider
        except SMSProviderError as exc:
            logger.warning("Twilio config rejected, falling back to noop: %s", exc)

    _default_provider = NoOpSMSProvider()
    logger.info("SMS provider: noop (no Twilio creds)")
    return _default_provider


def send_sms(
    *, to: str, body: str, sender: Optional[str] = None
) -> SMSResult:
    """High-level dispatch — pick the configured provider and send."""
    if not to or not body:
        raise SMSProviderError("Both 'to' and 'body' are required")
    return get_default_sms_provider().send(to=to, body=body, sender=sender)
