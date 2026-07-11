"""Payment domain models.

Each row is tenant-scoped via :class:`TenantScopedMixin` so the standard
session filter applies. Provider-side ids (``provider_intent_id``,
``provider_refund_id``, ``provider_event_id``) are the keys we use to
correlate webhooks back to our own rows.

The ``ProviderEvent`` table doubles as our webhook idempotency log: a
unique constraint on ``(provider, provider_event_id)`` plus
INSERT-then-process means a redelivered webhook is a no-op.
"""
from __future__ import annotations

import enum
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.mixins import TenantScopedMixin


class PaymentIntentStatus(str, enum.Enum):
    REQUIRES_PAYMENT_METHOD = "requires_payment_method"
    REQUIRES_CONFIRMATION = "requires_confirmation"
    REQUIRES_ACTION = "requires_action"
    PROCESSING = "processing"
    REQUIRES_CAPTURE = "requires_capture"
    SUCCEEDED = "succeeded"
    CANCELED = "canceled"
    FAILED = "failed"


class RefundStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class PaymentIntent(TenantScopedMixin, Base):
    __tablename__ = "payment_intents"
    __table_args__ = (
        UniqueConstraint(
            "provider", "provider_intent_id", name="uq_payment_intents_provider_id"
        ),
        Index(
            "ix_payment_intents_reservation",
            "tenant_id",
            "reservation_id",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(50), nullable=False, default="stripe")
    provider_intent_id = Column(String(120), nullable=False, index=True)
    client_secret = Column(String(255), nullable=True)

    reservation_id = Column(
        Integer, ForeignKey("reservations.id", ondelete="SET NULL"), nullable=True
    )
    guest_email = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)

    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="usd")
    status = Column(
        SQLEnum(PaymentIntentStatus),
        nullable=False,
        default=PaymentIntentStatus.REQUIRES_PAYMENT_METHOD,
    )

    captured_amount = Column(Numeric(12, 2), nullable=False, default=Decimal("0"))
    refunded_amount = Column(Numeric(12, 2), nullable=False, default=Decimal("0"))
    last_error = Column(Text, nullable=True)

    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    refunds = relationship("PaymentRefund", back_populates="intent")


class PaymentRefund(TenantScopedMixin, Base):
    __tablename__ = "payment_refunds"
    __table_args__ = (
        UniqueConstraint(
            "provider", "provider_refund_id", name="uq_payment_refunds_provider_id"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    intent_id = Column(
        Integer, ForeignKey("payment_intents.id", ondelete="CASCADE"), nullable=False
    )
    provider = Column(String(50), nullable=False, default="stripe")
    provider_refund_id = Column(String(120), nullable=False, index=True)

    amount = Column(Numeric(12, 2), nullable=False)
    status = Column(
        SQLEnum(RefundStatus), nullable=False, default=RefundStatus.PENDING
    )
    reason = Column(String(255), nullable=True)
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    intent = relationship("PaymentIntent", back_populates="refunds")


class ProviderEvent(TenantScopedMixin, Base):
    """Webhook idempotency log.

    We INSERT before processing; a duplicate webhook delivery hits the
    UNIQUE constraint and we treat it as a no-op.
    """

    __tablename__ = "payment_provider_events"
    __table_args__ = (
        UniqueConstraint(
            "provider", "provider_event_id", name="uq_provider_events_id"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(50), nullable=False, default="stripe")
    provider_event_id = Column(String(120), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)
    processed = Column(Boolean, nullable=False, default=False)
    received_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    processed_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)
