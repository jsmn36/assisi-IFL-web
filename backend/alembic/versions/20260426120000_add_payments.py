"""Add payment_intents, payment_refunds, payment_provider_events.

Revision ID: 20260426120000
Revises: 20260425190000
Create Date: 2026-04-26
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260426120000"
down_revision = "20260425190000"
branch_labels = None
depends_on = None


_PAYMENT_INTENT_STATUS = sa.Enum(
    "REQUIRES_PAYMENT_METHOD",
    "REQUIRES_CONFIRMATION",
    "REQUIRES_ACTION",
    "PROCESSING",
    "REQUIRES_CAPTURE",
    "SUCCEEDED",
    "CANCELED",
    "FAILED",
    name="paymentintentstatus",
)


_REFUND_STATUS = sa.Enum(
    "PENDING", "SUCCEEDED", "FAILED", "CANCELED", name="refundstatus"
)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("payment_intents"):
        op.create_table(
            "payment_intents",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column(
                "tenant_id",
                sa.Integer(),
                sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
                nullable=False,
                index=True,
            ),
            sa.Column("provider", sa.String(50), nullable=False, server_default="stripe"),
            sa.Column("provider_intent_id", sa.String(120), nullable=False, index=True),
            sa.Column("client_secret", sa.String(255), nullable=True),
            sa.Column(
                "reservation_id",
                sa.Integer(),
                sa.ForeignKey("reservations.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("guest_email", sa.String(255), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("amount", sa.Numeric(12, 2), nullable=False),
            sa.Column("currency", sa.String(3), nullable=False, server_default="usd"),
            sa.Column(
                "status",
                _PAYMENT_INTENT_STATUS,
                nullable=False,
                server_default="REQUIRES_PAYMENT_METHOD",
            ),
            sa.Column(
                "captured_amount", sa.Numeric(12, 2), nullable=False, server_default="0"
            ),
            sa.Column(
                "refunded_amount", sa.Numeric(12, 2), nullable=False, server_default="0"
            ),
            sa.Column("last_error", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.current_timestamp(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.current_timestamp(),
            ),
            sa.UniqueConstraint(
                "provider", "provider_intent_id", name="uq_payment_intents_provider_id"
            ),
        )
        op.create_index(
            "ix_payment_intents_reservation",
            "payment_intents",
            ["tenant_id", "reservation_id"],
        )

    if not inspector.has_table("payment_refunds"):
        op.create_table(
            "payment_refunds",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column(
                "tenant_id",
                sa.Integer(),
                sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
                nullable=False,
                index=True,
            ),
            sa.Column(
                "intent_id",
                sa.Integer(),
                sa.ForeignKey("payment_intents.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("provider", sa.String(50), nullable=False, server_default="stripe"),
            sa.Column("provider_refund_id", sa.String(120), nullable=False, index=True),
            sa.Column("amount", sa.Numeric(12, 2), nullable=False),
            sa.Column("status", _REFUND_STATUS, nullable=False, server_default="PENDING"),
            sa.Column("reason", sa.String(255), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.current_timestamp(),
            ),
            sa.UniqueConstraint(
                "provider", "provider_refund_id", name="uq_payment_refunds_provider_id"
            ),
        )

    if not inspector.has_table("payment_provider_events"):
        op.create_table(
            "payment_provider_events",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column(
                "tenant_id",
                sa.Integer(),
                sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
                nullable=False,
                index=True,
            ),
            sa.Column("provider", sa.String(50), nullable=False, server_default="stripe"),
            sa.Column("provider_event_id", sa.String(120), nullable=False, index=True),
            sa.Column("event_type", sa.String(100), nullable=False),
            sa.Column(
                "processed", sa.Boolean(), nullable=False, server_default=sa.text("0")
            ),
            sa.Column(
                "received_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.current_timestamp(),
            ),
            sa.Column("processed_at", sa.DateTime(), nullable=True),
            sa.Column("error", sa.Text(), nullable=True),
            sa.UniqueConstraint(
                "provider", "provider_event_id", name="uq_provider_events_id"
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("payment_provider_events"):
        op.drop_table("payment_provider_events")
    if inspector.has_table("payment_refunds"):
        op.drop_table("payment_refunds")
    if inspector.has_table("payment_intents"):
        op.drop_table("payment_intents")
    # SQLAlchemy creates the enum types lazily for SQLite; on Postgres
    # they need explicit cleanup. Wrapped in try/except for SQLite where
    # the type doesn't actually exist.
    try:
        _PAYMENT_INTENT_STATUS.drop(bind, checkfirst=True)
    except Exception:
        pass
    try:
        _REFUND_STATUS.drop(bind, checkfirst=True)
    except Exception:
        pass
