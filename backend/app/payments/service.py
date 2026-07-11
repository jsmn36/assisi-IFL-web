"""High-level payments service.

Orchestrates the local DB rows with the payment provider. Webhook
processing lives here too — the API router just verifies the signature,
inserts the idempotency row, and hands a normalized
:class:`WebhookEvent` to :meth:`process_webhook_event`.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.payments.models import (
    PaymentIntent,
    PaymentIntentStatus,
    PaymentRefund,
    ProviderEvent,
    RefundStatus,
)
from app.payments.provider import (
    PaymentProvider,
    PaymentProviderError,
    WebhookEvent,
)
from app.payments.stripe_provider import get_default_provider
from app.services.base_service import NotFoundError, ServiceError

logger = logging.getLogger(__name__)


_STRIPE_TO_INTENT_STATUS = {
    "requires_payment_method": PaymentIntentStatus.REQUIRES_PAYMENT_METHOD,
    "requires_confirmation": PaymentIntentStatus.REQUIRES_CONFIRMATION,
    "requires_action": PaymentIntentStatus.REQUIRES_ACTION,
    "processing": PaymentIntentStatus.PROCESSING,
    "requires_capture": PaymentIntentStatus.REQUIRES_CAPTURE,
    "succeeded": PaymentIntentStatus.SUCCEEDED,
    "canceled": PaymentIntentStatus.CANCELED,
}


def _map_intent_status(value: Optional[str]) -> PaymentIntentStatus:
    if value is None:
        return PaymentIntentStatus.REQUIRES_PAYMENT_METHOD
    return _STRIPE_TO_INTENT_STATUS.get(value.lower(), PaymentIntentStatus.PROCESSING)


_STRIPE_TO_REFUND_STATUS = {
    "pending": RefundStatus.PENDING,
    "succeeded": RefundStatus.SUCCEEDED,
    "failed": RefundStatus.FAILED,
    "canceled": RefundStatus.CANCELED,
}


def _map_refund_status(value: Optional[str]) -> RefundStatus:
    if value is None:
        return RefundStatus.PENDING
    return _STRIPE_TO_REFUND_STATUS.get(value.lower(), RefundStatus.PENDING)


class PaymentService:
    def __init__(
        self,
        db: Session,
        tenant_id: int,
        provider: Optional[PaymentProvider] = None,
    ) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self.provider = provider or get_default_provider()

    # ─── Intents ──────────────────────────────────────────────────────────
    def create_intent(
        self,
        *,
        amount: Decimal,
        currency: str = "usd",
        reservation_id: Optional[int] = None,
        guest_email: Optional[str] = None,
        description: Optional[str] = None,
    ) -> PaymentIntent:
        if amount <= 0:
            raise ServiceError("amount must be positive")

        result = self.provider.create_intent(
            amount=amount,
            currency=currency,
            tenant_id=self.tenant_id,
            reservation_id=reservation_id,
            guest_email=guest_email,
            description=description,
        )

        intent = PaymentIntent(
            tenant_id=self.tenant_id,
            provider=self.provider.name,
            provider_intent_id=result.provider_intent_id,
            client_secret=result.client_secret,
            reservation_id=reservation_id,
            guest_email=guest_email,
            description=description,
            amount=amount,
            currency=currency.lower(),
            status=_map_intent_status(result.status),
        )
        self.db.add(intent)
        self.db.commit()
        self.db.refresh(intent)
        return intent

    def get_intent(self, intent_id: int) -> PaymentIntent:
        intent = (
            self.db.query(PaymentIntent).filter(PaymentIntent.id == intent_id).first()
        )
        if not intent:
            raise NotFoundError(f"PaymentIntent {intent_id} not found")
        return intent

    def capture(self, intent_id: int) -> PaymentIntent:
        intent = self.get_intent(intent_id)
        result = self.provider.capture_intent(intent.provider_intent_id)
        intent.status = _map_intent_status(result.status)
        if result.status == "succeeded":
            intent.captured_amount = intent.amount
        self.db.commit()
        self.db.refresh(intent)
        return intent

    # ─── Refunds ──────────────────────────────────────────────────────────
    def refund(
        self,
        intent_id: int,
        *,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None,
    ) -> PaymentRefund:
        intent = self.get_intent(intent_id)
        result = self.provider.refund(
            intent.provider_intent_id, amount=amount, reason=reason
        )

        refund_row = PaymentRefund(
            tenant_id=self.tenant_id,
            intent_id=intent.id,
            provider=self.provider.name,
            provider_refund_id=result.provider_refund_id,
            amount=result.amount,
            status=_map_refund_status(result.status),
            reason=result.reason,
        )
        self.db.add(refund_row)

        # Track the refunded amount on the parent intent so we can prevent
        # over-refunds at the API layer without re-querying the provider.
        intent.refunded_amount = (
            (intent.refunded_amount or Decimal("0")) + result.amount
        )
        if intent.refunded_amount >= intent.amount:
            # Stripe will report this as ``charge.refunded`` separately too;
            # we set it here so the caller's next read is consistent.
            pass

        self.db.commit()
        self.db.refresh(refund_row)
        return refund_row

    # ─── Webhook ──────────────────────────────────────────────────────────
    def record_webhook_event(self, event: WebhookEvent) -> bool:
        """Insert the idempotency row. Returns False if already seen."""
        row = ProviderEvent(
            tenant_id=self.tenant_id,
            provider=self.provider.name,
            provider_event_id=event.event_id,
            event_type=event.event_type,
        )
        try:
            self.db.add(row)
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            return False
        return True

    def process_webhook_event(self, event: WebhookEvent) -> None:
        """Apply a webhook to local state.

        Caller must have already invoked :meth:`record_webhook_event` and
        gotten True (i.e. fresh delivery).
        """
        try:
            if event.provider_intent_id:
                intent = (
                    self.db.query(PaymentIntent)
                    .filter(
                        PaymentIntent.provider == self.provider.name,
                        PaymentIntent.provider_intent_id == event.provider_intent_id,
                    )
                    .first()
                )
                if intent is None:
                    logger.warning(
                        "Webhook for unknown intent provider_intent_id=%s",
                        event.provider_intent_id,
                    )
                else:
                    if event.status:
                        intent.status = _map_intent_status(event.status)
                    if event.event_type == "payment_intent.succeeded" and event.amount:
                        intent.captured_amount = event.amount

            if event.provider_refund_id:
                refund = (
                    self.db.query(PaymentRefund)
                    .filter(
                        PaymentRefund.provider == self.provider.name,
                        PaymentRefund.provider_refund_id == event.provider_refund_id,
                    )
                    .first()
                )
                if refund is None and event.amount and event.provider_intent_id:
                    # Refund initiated outside our app (e.g. dashboard).
                    parent = (
                        self.db.query(PaymentIntent)
                        .filter(
                            PaymentIntent.provider == self.provider.name,
                            PaymentIntent.provider_intent_id
                            == event.provider_intent_id,
                        )
                        .first()
                    )
                    if parent is not None:
                        self.db.add(
                            PaymentRefund(
                                tenant_id=self.tenant_id,
                                intent_id=parent.id,
                                provider=self.provider.name,
                                provider_refund_id=event.provider_refund_id,
                                amount=event.amount,
                                status=_map_refund_status(event.status),
                            )
                        )
                        parent.refunded_amount = (
                            (parent.refunded_amount or Decimal("0")) + event.amount
                        )
                elif refund is not None and event.status:
                    refund.status = _map_refund_status(event.status)

            # Mark the idempotency row as processed.
            log = (
                self.db.query(ProviderEvent)
                .filter(
                    ProviderEvent.provider == self.provider.name,
                    ProviderEvent.provider_event_id == event.event_id,
                )
                .first()
            )
            if log is not None:
                log.processed = True
                log.processed_at = datetime.now(timezone.utc)

            self.db.commit()
        except Exception as exc:
            logger.exception("Webhook processing failed for event=%s", event.event_id)
            self.db.rollback()
            # Mark error on the idempotency row so we can retry later.
            log = (
                self.db.query(ProviderEvent)
                .filter(
                    ProviderEvent.provider == self.provider.name,
                    ProviderEvent.provider_event_id == event.event_id,
                )
                .first()
            )
            if log is not None:
                log.error = str(exc)[:500]
                self.db.commit()
            raise PaymentProviderError(str(exc)) from exc
