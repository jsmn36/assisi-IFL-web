"""Tier 1 features: suppressions, compliance calendar, audit findings.

Revision ID: tier1_2026_05_12
Revises: 20260426120000
Create Date: 2026-05-12

Adds three new tables backing the Tier 1 features that live in the main
PMS database:
  - notification_suppressions  (suppression list)
  - compliance_calendar_items  (compliance calendar)
  - audit_findings + audit_finding_activity (audit finding tracker)
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision: str = "tier1_2026_05_12"
down_revision: Union[str, None] = "20260426120000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # notification_suppressions
    # ------------------------------------------------------------------
    op.create_table(
        "notification_suppressions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("address", sa.String(length=255), nullable=False),
        sa.Column(
            "channel",
            sa.Enum("email", "sms", "all", name="suppressionchannel"),
            nullable=False,
        ),
        sa.Column(
            "reason",
            sa.Enum(
                "unsubscribe",
                "bounce",
                "complaint",
                "manual",
                "gdpr_erasure",
                "invalid",
                name="suppressionreason",
            ),
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
    )
    op.create_index(
        "ix_suppressions_address_channel",
        "notification_suppressions",
        ["address", "channel"],
        unique=True,
    )
    op.create_index(
        "ix_suppressions_created_at",
        "notification_suppressions",
        ["created_at"],
    )
    op.create_index(
        "ix_notification_suppressions_address",
        "notification_suppressions",
        ["address"],
    )

    # ------------------------------------------------------------------
    # compliance_calendar_items
    # ------------------------------------------------------------------
    op.create_table(
        "compliance_calendar_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "category",
            sa.Enum(
                "license",
                "filing",
                "renewal",
                "audit",
                "training",
                "policy",
                "other",
                name="complianceitemcategory",
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "open",
                "in_progress",
                "done",
                "overdue",
                "waived",
                name="complianceitemstatus",
            ),
            nullable=False,
            index=True,
        ),
        sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("recurrence_months", sa.Integer(), nullable=True),
        sa.Column("reminder_90d_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reminder_30d_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reminder_7d_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("completion_evidence_url", sa.String(length=500), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
    )

    # ------------------------------------------------------------------
    # audit_findings
    # ------------------------------------------------------------------
    op.create_table(
        "audit_findings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("reference", sa.String(length=50), nullable=True, index=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "source",
            sa.Enum(
                "internal_audit",
                "external_audit",
                "regulator",
                "self_reported",
                "pen_test",
                "incident",
                name="findingsource",
            ),
            nullable=False,
        ),
        sa.Column(
            "severity",
            sa.Enum("low", "medium", "high", "critical", name="findingseverity"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "open",
                "in_remediation",
                "awaiting_verification",
                "closed",
                "overdue",
                "escalated",
                name="findingstatus",
            ),
            nullable=False,
            index=True,
        ),
        sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True, index=True),
        sa.Column("escalated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("escalated_to_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("resolution_summary", sa.Text(), nullable=True),
        sa.Column("evidence_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
    )

    op.create_table(
        "audit_finding_activity",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column(
            "finding_id",
            sa.Integer(),
            sa.ForeignKey("audit_findings.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("payload", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("audit_finding_activity")
    op.drop_table("audit_findings")
    op.drop_table("compliance_calendar_items")
    op.drop_index("ix_notification_suppressions_address", table_name="notification_suppressions")
    op.drop_index("ix_suppressions_created_at", table_name="notification_suppressions")
    op.drop_index("ix_suppressions_address_channel", table_name="notification_suppressions")
    op.drop_table("notification_suppressions")
    # SQLite doesn't support ENUM type drops; on Postgres these would need:
    # op.execute("DROP TYPE IF EXISTS suppressionchannel")
    # op.execute("DROP TYPE IF EXISTS suppressionreason")
    # etc. — left commented for portability.
