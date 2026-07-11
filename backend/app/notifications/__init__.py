"""Notification dispatch channels — email, SMS.

Email is handled elsewhere (Jinja templates + SMTP). This package adds
the SMS channel. The ``SMSProvider`` protocol is the extension point;
:func:`send_sms` is the high-level entry point that picks the configured
provider and dispatches.
"""
from app.notifications.sms_provider import (
    SMSProvider,
    SMSProviderError,
    SMSResult,
    send_sms,
)

__all__ = ["SMSProvider", "SMSProviderError", "SMSResult", "send_sms"]
