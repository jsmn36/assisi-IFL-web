"""Tier 3 features: GBC, DAL, filter templates.

Revision ID: tier3_2026_05_14
Revises: tier2_2026_05_13
Create Date: 2026-05-14

Adds the main-DB tables for Tier 3 features:
  - ghost_booking_scores
  - decision_audit_entries / overrides / outcomes
  - filter_templates / filter_template_uses

Accounting-DB tables (close_cycles, close_tasks, close_exceptions,
cash_forecast_snapshots, cash_forecast_lines, ledger_drift_alerts) are
picked up automatically by ``init_accounting_db -> create_all``.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "tier3_2026_05_14"
down_revision: Union[str, None] = "tier2_2026_05_13"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ----- Ghost Booking Classifier -----
    op.create_table(
        "ghost_booking_scores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("reservation_id", sa.Integer(), sa.ForeignKey("reservations.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("guest_id", sa.Integer(), sa.ForeignKey("guests.id"), nullable=True, index=True),
        sa.Column("risk_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "risk_tier",
            sa.Enum("low", "medium", "high", "block", name="ghostrisktier"),
            nullable=False,
        ),
        sa.Column(
            "decision",
            sa.Enum("allow", "require_deposit", "require_review", "block", name="ghostdecision"),
            nullable=False,
        ),
        sa.Column("signals_snapshot", sa.JSON(), nullable=False),
        sa.Column("contributions", sa.JSON(), nullable=False),
        sa.Column("overridden_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("overridden_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("override_reason", sa.String(500), nullable=True),
        sa.Column(
            "override_decision",
            sa.Enum("allow", "require_deposit", "require_review", "block", name="ghostdecision", create_type=False),
            nullable=True,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_ghost_score_reservation", "ghost_booking_scores", ["reservation_id"])
    op.create_index("ix_ghost_score_created", "ghost_booking_scores", ["created_at"])

    # ----- Decision Audit Ledger -----
    op.create_table(
        "decision_audit_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("feature_id", sa.String(100), nullable=False, index=True),
        sa.Column("decision_type", sa.String(100), nullable=False),
        sa.Column("outcome", sa.String(100), nullable=False),
        sa.Column("inputs", sa.JSON(), nullable=False),
        sa.Column("contributions", sa.JSON(), nullable=True),
        sa.Column("model_version", sa.String(50), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("resource_kind", sa.String(50), nullable=True),
        sa.Column("resource_id", sa.String(100), nullable=True),
        sa.Column("correlation_id", sa.String(100), nullable=True, index=True),
        sa.Column(
            "status",
            sa.Enum("pending_outcome", "outcome_recorded", name="daldecisionstatus"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_dal_feature_created", "decision_audit_entries", ["feature_id", "created_at"])
    op.create_index("ix_dal_resource", "decision_audit_entries", ["resource_kind", "resource_id"])

    op.create_table(
        "decision_audit_overrides",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("decision_entry_id", sa.Integer(), sa.ForeignKey("decision_audit_entries.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("original_outcome", sa.String(100), nullable=False),
        sa.Column("new_outcome", sa.String(100), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "decision_audit_outcomes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("decision_entry_id", sa.Integer(), sa.ForeignKey("decision_audit_entries.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("outcome_label", sa.String(100), nullable=False),
        sa.Column("outcome_value", sa.JSON(), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
    )

    # ----- Filter templates -----
    op.create_table(
        "filter_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("primary_entity", sa.String(50), nullable=False),
        sa.Column("entity_types", sa.JSON(), nullable=False),
        sa.Column("filter_spec", sa.JSON(), nullable=False),
        sa.Column("role_visibility", sa.JSON(), nullable=False),
        sa.Column(
            "visibility",
            sa.Enum("private", "team", "property", name="templatevisibility"),
            nullable=False,
        ),
        sa.Column("pinned_to", sa.JSON(), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("use_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("slug", "tenant_id", name="uq_filter_template_slug"),
    )
    op.create_index("ix_filter_template_entity", "filter_templates", ["primary_entity"])
    op.create_table(
        "filter_template_uses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("template_id", sa.Integer(), sa.ForeignKey("filter_templates.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("entity_view", sa.String(50), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_filter_template_use_template_user", "filter_template_uses", ["template_id", "user_id"])


def downgrade() -> None:
    for t in [
        "filter_template_uses",
        "filter_templates",
        "decision_audit_outcomes",
        "decision_audit_overrides",
        "decision_audit_entries",
        "ghost_booking_scores",
    ]:
        op.drop_table(t)
