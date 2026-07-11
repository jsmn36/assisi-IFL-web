"""Payments REST API.

Endpoints (all require an authenticated tenant-scoped session):

  POST /api/v1/payments/intents          create + persist a PaymentIntent
  GET  /api/v1/payments/intents/{id}     read one
  POST /api/v1/payments/intents/{id}/capture
  POST /api/v1/payments/intents/{id}/refund
  POST /api/v1/payments/webhooks/stripe  Stripe webhook (no auth — signature only)
"""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_tenant_id, get_current_user, get_db
from app.payments.models import PaymentIntent, PaymentRefund
from app.payments.provider import PaymentProviderError
from app.payments.service import PaymentService
from app.payments.stripe_provider import get_default_provider
from app.services.base_service import NotFoundError

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/payments", tags=["Payments"])


class CreateIntentRequest(BaseModel):
    amount: Decimal = Field(..., gt=0)
    currency: str = "usd"
    reservation_id: Optional[int] = None
    guest_email: Optional[str] = None
    description: Optional[str] = None


class RefundRequest(BaseModel):
    amount: Optional[Decimal] = Field(default=None, gt=0)
    reason: Optional[str] = None


class IntentOut(BaseModel):
    id: int
    provider: str
    provider_intent_id: str
    client_secret: Optional[str] = None
    reservation_id: Optional[int] = None
    amount: Decimal
    currency: str
    status: str
    captured_amount: Decimal
    refunded_amount: Decimal

    model_config = ConfigDict(from_attributes=True)


class RefundOut(BaseModel):
    id: int
    intent_id: int
    provider: str
    provider_refund_id: str
    amount: Decimal
    status: str
    reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


def _intent_out(intent: PaymentIntent) -> IntentOut:
    return IntentOut(
        id=intent.id,
        provider=intent.provider,
        provider_intent_id=intent.provider_intent_id,
        client_secret=intent.client_secret,
        reservation_id=intent.reservation_id,
        amount=intent.amount,
        currency=intent.currency,
        status=intent.status.value if hasattr(intent.status, "value") else str(intent.status),
        captured_amount=intent.captured_amount,
        refunded_amount=intent.refunded_amount,
    )


@router.post(
    "/intents",
    response_model=IntentOut,
    status_code=status.HTTP_201_CREATED,
)
def create_intent(
    payload: CreateIntentRequest,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
    _user=Depends(get_current_user),
):
    service = PaymentService(db, tenant_id)
    try:
        intent = service.create_intent(
            amount=payload.amount,
            currency=payload.currency,
            reservation_id=payload.reservation_id,
            guest_email=payload.guest_email,
            description=payload.description,
        )
    except PaymentProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return _intent_out(intent)


@router.get("/intents/{intent_id}", response_model=IntentOut)
def read_intent(
    intent_id: int,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
    _user=Depends(get_current_user),
):
    service = PaymentService(db, tenant_id)
    try:
        intent = service.get_intent(intent_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="PaymentIntent not found")
    return _intent_out(intent)


@router.post("/intents/{intent_id}/capture", response_model=IntentOut)
def capture(
    intent_id: int,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
    _user=Depends(get_current_user),
):
    service = PaymentService(db, tenant_id)
    try:
        intent = service.capture(intent_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="PaymentIntent not found")
    except PaymentProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return _intent_out(intent)


@router.post(
    "/intents/{intent_id}/refund",
    response_model=RefundOut,
    status_code=status.HTTP_201_CREATED,
)
def refund(
    intent_id: int,
    payload: RefundRequest,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
    _user=Depends(get_current_user),
):
    service = PaymentService(db, tenant_id)
    try:
        intent = service.get_intent(intent_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="PaymentIntent not found")

    refund_amount = payload.amount or intent.amount
    if intent.refunded_amount + refund_amount > intent.amount:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Refund would exceed captured amount: "
                f"already refunded {intent.refunded_amount}, "
                f"trying to add {refund_amount}, total {intent.amount}"
            ),
        )

    try:
        refund_row = service.refund(
            intent_id=intent.id, amount=payload.amount, reason=payload.reason
        )
    except PaymentProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    return RefundOut(
        id=refund_row.id,
        intent_id=refund_row.intent_id,
        provider=refund_row.provider,
        provider_refund_id=refund_row.provider_refund_id,
        amount=refund_row.amount,
        status=refund_row.status.value if hasattr(refund_row.status, "value") else str(refund_row.status),
        reason=refund_row.reason,
    )


# ─── Webhook ───────────────────────────────────────────────────────────────
# This endpoint is whitelisted in the tenant middleware (no JWT). Tenant
# is resolved from the PaymentIntent metadata stamped at create time.


@router.post("/webhooks/stripe", include_in_schema=False)
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    body = await request.body()
    sig = request.headers.get("stripe-signature")

    provider = get_default_provider()
    try:
        event = provider.parse_webhook(body, sig)
    except PaymentProviderError as exc:
        # Verification failure is not retryable — return 400 so Stripe stops.
        logger.warning("Stripe webhook rejected: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))

    # Resolve tenant from the original PaymentIntent. We bypass the row
    # filter because the webhook hits us with no tenant context yet.
    from app.core.tenant_context import bypass_tenant_filter, tenant_scope

    tenant_id: Optional[int] = None
    if event.provider_intent_id:
        with bypass_tenant_filter():
            row = (
                db.query(PaymentIntent)
                .filter(
                    PaymentIntent.provider == "stripe",
                    PaymentIntent.provider_intent_id == event.provider_intent_id,
                )
                .first()
            )
            if row is not None:
                tenant_id = row.tenant_id

    if tenant_id is None:
        # Try metadata as a fallback (set when we created the intent).
        try:
            tenant_id = int(
                event.raw.get("data", {}).get("object", {})
                .get("metadata", {})
                .get("tenant_id")
            )
        except (TypeError, ValueError):
            tenant_id = None

    if tenant_id is None:
        logger.warning(
            "Stripe webhook event=%s could not be routed to a tenant", event.event_id
        )
        # Still record so we don't keep getting redelivered.
        return {"received": True, "routed": False}

    with tenant_scope(tenant_id):
        service = PaymentService(db, tenant_id)
        is_fresh = service.record_webhook_event(event)
        if not is_fresh:
            return {"received": True, "duplicate": True}
        try:
            service.process_webhook_event(event)
        except PaymentProviderError as exc:
            # Return 500 so Stripe retries this delivery.
            raise HTTPException(status_code=500, detail=str(exc))

    return {"received": True}
