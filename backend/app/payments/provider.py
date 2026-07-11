"""PaymentProvider — extension point for non-Stripe providers.

The contract is intentionally small: an opaque ``provider_intent_id`` is
the only thing we persist that ties our PaymentIntent row to whatever
the provider knows about. Webhook signatures and idempotency are the
provider's responsibility (Stripe gives us both for free; a future
adapter for Razorpay/Square would re-implement them).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, Optional, Protocol


class PaymentProviderError(Exception):
    """Wraps SDK-level errors so callers don't depend on a specific SDK."""


@dataclass
class PaymentIntentResult:
    """Returned from :meth:`PaymentProvider.create_intent`."""

    provider_intent_id: str
    client_secret: Optional[str] = None
    status: str = "requires_payment_method"
    amount: Decimal = Decimal("0")
    currency: str = "usd"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RefundResult:
    provider_refund_id: str
    provider_intent_id: str
    amount: Decimal
    status: str
    reason: Optional[str] = None


@dataclass
class WebhookEvent:
    """Normalized webhook payload — every provider maps onto this shape."""

    event_id: str
    event_type: str  # e.g. "payment_intent.succeeded"
    provider_intent_id: Optional[str]
    provider_refund_id: Optional[str] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    status: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)


class PaymentProvider(Protocol):
    """Plug-point for payment processors. Stripe is the reference impl."""

    name: str

    def create_intent(
        self,
        *,
        amount: Decimal,
        currency: str,
        tenant_id: int,
        reservation_id: Optional[int] = None,
        guest_email: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PaymentIntentResult:
        ...

    def capture_intent(self, provider_intent_id: str) -> PaymentIntentResult:
        ...

    def refund(
        self,
        provider_intent_id: str,
        *,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None,
    ) -> RefundResult:
        ...

    def parse_webhook(
        self, body: bytes, signature_header: Optional[str]
    ) -> WebhookEvent:
        """Verify the signature and return a normalized WebhookEvent.

        Raises :class:`PaymentProviderError` if verification fails.
        """
        ...
