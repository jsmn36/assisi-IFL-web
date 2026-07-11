"""Stripe implementation of :class:`PaymentProvider`.

Soft-imports ``stripe`` so the rest of the app boots even on dev boxes
without the SDK installed (errors only at the first call site). Reads
``STRIPE_SECRET_KEY`` and ``STRIPE_WEBHOOK_SECRET`` from settings — both
are optional in dev (the module raises only when the SDK is actually
exercised).

Amount handling: our API works in normal currency units (e.g. USD
dollars as Decimal). Stripe wants the smallest unit (cents). We do the
multiplication here so callers never see ``cents`` in their code.
"""
from __future__ import annotations

import logging
import os
from decimal import Decimal
from typing import Any, Dict, Optional

from app.payments.provider import (
    PaymentIntentResult,
    PaymentProvider,
    PaymentProviderError,
    RefundResult,
    WebhookEvent,
)

logger = logging.getLogger(__name__)


# Currencies where the smallest unit equals the major unit (no cents).
# Stripe's minor-unit rules — keep the list narrow; expand as needed.
_ZERO_DECIMAL_CURRENCIES = frozenset(
    {"bif", "clp", "djf", "gnf", "jpy", "kmf", "krw", "mga", "pyg", "rwf", "ugx", "vnd", "vuv", "xaf", "xof", "xpf"}
)


def _to_minor(amount: Decimal, currency: str) -> int:
    if currency.lower() in _ZERO_DECIMAL_CURRENCIES:
        return int(amount)
    return int((amount * 100).quantize(Decimal("1")))


def _from_minor(amount: int, currency: str) -> Decimal:
    if currency.lower() in _ZERO_DECIMAL_CURRENCIES:
        return Decimal(amount)
    return (Decimal(amount) / Decimal(100)).quantize(Decimal("0.01"))


def _stripe_module():
    """Lazily import the ``stripe`` SDK with a friendly error."""
    try:
        import stripe  # type: ignore[import-not-found]
    except ImportError as exc:
        raise PaymentProviderError(
            "stripe SDK not installed. Add `stripe>=8.0.0` to requirements.txt."
        ) from exc

    secret = os.environ.get("STRIPE_SECRET_KEY", "").strip()
    if not secret:
        raise PaymentProviderError(
            "STRIPE_SECRET_KEY env var is not set. Configure it before calling Stripe."
        )
    stripe.api_key = secret
    return stripe


class StripeProvider:
    name = "stripe"

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
        stripe = _stripe_module()

        payload_metadata: Dict[str, Any] = {"tenant_id": str(tenant_id)}
        if reservation_id is not None:
            payload_metadata["reservation_id"] = str(reservation_id)
        if metadata:
            for key, value in metadata.items():
                payload_metadata[str(key)[:40]] = str(value)[:500]

        try:
            intent = stripe.PaymentIntent.create(
                amount=_to_minor(amount, currency),
                currency=currency.lower(),
                description=description,
                receipt_email=guest_email,
                automatic_payment_methods={"enabled": True},
                metadata=payload_metadata,
            )
        except Exception as exc:  # stripe.error.StripeError + transport errors
            logger.exception("Stripe create_intent failed")
            raise PaymentProviderError(str(exc)) from exc

        return PaymentIntentResult(
            provider_intent_id=intent.id,
            client_secret=intent.client_secret,
            status=intent.status,
            amount=_from_minor(intent.amount, intent.currency),
            currency=intent.currency,
            metadata=dict(intent.metadata or {}),
        )

    def capture_intent(self, provider_intent_id: str) -> PaymentIntentResult:
        stripe = _stripe_module()
        try:
            intent = stripe.PaymentIntent.capture(provider_intent_id)
        except Exception as exc:
            logger.exception("Stripe capture_intent failed")
            raise PaymentProviderError(str(exc)) from exc
        return PaymentIntentResult(
            provider_intent_id=intent.id,
            client_secret=intent.client_secret,
            status=intent.status,
            amount=_from_minor(intent.amount, intent.currency),
            currency=intent.currency,
            metadata=dict(intent.metadata or {}),
        )

    def refund(
        self,
        provider_intent_id: str,
        *,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None,
    ) -> RefundResult:
        stripe = _stripe_module()
        kwargs: Dict[str, Any] = {"payment_intent": provider_intent_id}
        if amount is not None:
            # We don't yet know the currency here without fetching, so trust
            # the caller has stored it consistently (USD default).
            kwargs["amount"] = _to_minor(amount, "usd")
        if reason:
            # Stripe accepts only a small enum here; pass through if it matches.
            if reason in {"duplicate", "fraudulent", "requested_by_customer"}:
                kwargs["reason"] = reason
        try:
            refund = stripe.Refund.create(**kwargs)
        except Exception as exc:
            logger.exception("Stripe refund failed")
            raise PaymentProviderError(str(exc)) from exc
        return RefundResult(
            provider_refund_id=refund.id,
            provider_intent_id=provider_intent_id,
            amount=_from_minor(refund.amount, refund.currency),
            status=refund.status,
            reason=getattr(refund, "reason", None),
        )

    def parse_webhook(
        self, body: bytes, signature_header: Optional[str]
    ) -> WebhookEvent:
        stripe = _stripe_module()
        webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "").strip()
        if not webhook_secret:
            raise PaymentProviderError(
                "STRIPE_WEBHOOK_SECRET env var is not set; refusing to process webhook"
            )
        if not signature_header:
            raise PaymentProviderError("Missing Stripe-Signature header")

        try:
            event = stripe.Webhook.construct_event(
                payload=body,
                sig_header=signature_header,
                secret=webhook_secret,
            )
        except Exception as exc:  # SignatureVerificationError + transport
            raise PaymentProviderError(f"Invalid Stripe signature: {exc}") from exc

        data = event.get("data", {}).get("object", {}) or {}
        currency = data.get("currency")
        amount_minor = data.get("amount") or data.get("amount_refunded")
        amount = _from_minor(amount_minor, currency) if (amount_minor and currency) else None

        # PaymentIntent events expose ``id``; refund events expose ``payment_intent``.
        provider_intent_id = data.get("id") if event["type"].startswith("payment_intent.") else data.get("payment_intent")
        provider_refund_id = data.get("id") if event["type"].startswith("charge.refund.") or event["type"].startswith("refund.") else None

        return WebhookEvent(
            event_id=event["id"],
            event_type=event["type"],
            provider_intent_id=provider_intent_id,
            provider_refund_id=provider_refund_id,
            amount=amount,
            currency=currency,
            status=data.get("status"),
            raw=dict(event),
        )


_default_provider: Optional[StripeProvider] = None


def get_default_provider() -> PaymentProvider:
    """Return the process-wide default provider (Stripe)."""
    global _default_provider
    if _default_provider is None:
        _default_provider = StripeProvider()
    return _default_provider
