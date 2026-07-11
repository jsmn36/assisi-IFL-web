"""Payments package.

Public surface used by callers:
  - PaymentService (high-level: create intent, capture, refund)
  - PaymentProvider (extension point for non-Stripe providers)

Models live in :mod:`app.payments.models`; the API router is in
:mod:`app.payments.api`. Webhooks are mounted from
:mod:`app.payments.webhooks`.
"""
from app.payments.provider import (
    PaymentProvider,
    PaymentIntentResult,
    RefundResult,
    WebhookEvent,
    PaymentProviderError,
)
from app.payments.service import PaymentService

__all__ = [
    "PaymentProvider",
    "PaymentIntentResult",
    "RefundResult",
    "WebhookEvent",
    "PaymentProviderError",
    "PaymentService",
]
