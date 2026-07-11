"""Tier 2 features: anomalies, upsells, feedback, JIT, corporate, DSAR, consent, allocations.

Revision ID: tier2_2026_05_13
Revises: tier1_2026_05_12
Create Date: 2026-05-13

Creates the new main-DB tables backing Tier 2:
  - kpi_baselines, anomaly_alerts, anomaly_mutes
  - upsell_chains, upsell_steps, upsell_chain_runs, upsell_sends
  - guest_feedback, feedback_resolutions
  - jit_access_grants, jit_access_activity
  - corporate_accounts, corporate_memberships
  - dsar_requests, consent_versions, consent_records
  - room_allocations, channel_buffers, room_holds
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "tier2_2026_05_13"
down_revision: Union[str, None] = "tier1_2026_05_12"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ----- Anomaly detection -----
    op.create_table(
        "kpi_baselines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("metric_key", sa.String(100), nullable=False, index=True),
        sa.Column("scope", sa.String(100), nullable=False, server_default="all"),
        sa.Column("mean", sa.Float(), nullable=False, server_default="0"),
        sa.Column("stdev", sa.Float(), nullable=False, server_default="0"),
        sa.Column("sample_size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("window_days", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("last_recomputed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("metric_key", "scope", "tenant_id", name="uq_kpi_baseline_scope"),
    )

    op.create_table(
        "anomaly_alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("metric_key", sa.String(100), nullable=False),
        sa.Column("scope", sa.String(100), nullable=False, server_default="all"),
        sa.Column("observed_value", sa.Numeric(14, 4), nullable=False),
        sa.Column("baseline_mean", sa.Float(), nullable=False),
        sa.Column("baseline_stdev", sa.Float(), nullable=False),
        sa.Column("z_score", sa.Float(), nullable=False),
        sa.Column("direction", sa.String(10), nullable=False),
        sa.Column(
            "severity",
            sa.Enum("info", "warning", "critical", name="anomalyseverity"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "open", "acknowledged", "muted", "false_positive", "resolved",
                name="anomalystatus",
            ),
            nullable=False,
        ),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("root_cause_hint", sa.Text(), nullable=True),
        sa.Column("suggested_action", sa.Text(), nullable=True),
        sa.Column("acknowledged_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_anomaly_alerts_metric_created", "anomaly_alerts", ["metric_key", "created_at"])
    op.create_index("ix_anomaly_alerts_status", "anomaly_alerts", ["status"])

    op.create_table(
        "anomaly_mutes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("metric_key", sa.String(100), nullable=False, index=True),
        sa.Column("scope", sa.String(100), nullable=False, server_default="all"),
        sa.Column("reason", sa.String(255), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ----- Upsell chains -----
    op.create_table(
        "upsell_chains",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "trigger",
            sa.Enum(
                "reservation.confirmed",
                "reservation.cancelled",
                "stay.checked_in",
                "stay.checked_out",
                "pre_arrival_24h",
                "post_stay_24h",
                name="upselltrigger",
            ),
            nullable=False,
            index=True,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("conditions", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "upsell_steps",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("chain_id", sa.Integer(), sa.ForeignKey("upsell_chains.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column(
            "step_type",
            sa.Enum("email", "sms", "note", name="upsellsteptype"),
            nullable=False,
        ),
        sa.Column("delay_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("subject", sa.String(255), nullable=True),
        sa.Column("body_template", sa.Text(), nullable=False),
    )
    op.create_table(
        "upsell_chain_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("chain_id", sa.Integer(), sa.ForeignKey("upsell_chains.id"), nullable=False, index=True),
        sa.Column("trigger_event", sa.String(50), nullable=False),
        sa.Column("guest_id", sa.Integer(), sa.ForeignKey("guests.id"), nullable=True, index=True),
        sa.Column("reservation_id", sa.Integer(), sa.ForeignKey("reservations.id"), nullable=True, index=True),
        sa.Column(
            "status",
            sa.Enum("pending", "running", "completed", "cancelled", "failed", name="upsellrunstatus"),
            nullable=False,
        ),
        sa.Column("next_step_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_step_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_upsell_run_status_next", "upsell_chain_runs", ["status", "next_step_at"])
    op.create_table(
        "upsell_sends",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("upsell_chain_runs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("step_id", sa.Integer(), sa.ForeignKey("upsell_steps.id"), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("recipient", sa.String(255), nullable=True),
        sa.Column("suppressed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
    )

    # ----- Feedback -----
    op.create_table(
        "guest_feedback",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("guest_id", sa.Integer(), sa.ForeignKey("guests.id"), nullable=True, index=True),
        sa.Column("reservation_id", sa.Integer(), sa.ForeignKey("reservations.id"), nullable=True, index=True),
        sa.Column(
            "channel",
            sa.Enum(
                "post_stay_survey", "in_app", "email_reply", "social", "manual",
                name="feedbackchannel",
            ),
            nullable=False,
        ),
        sa.Column("nps_score", sa.Integer(), nullable=True),
        sa.Column("rating_1_5", sa.Integer(), nullable=True),
        sa.Column(
            "sentiment",
            sa.Enum("positive", "neutral", "negative", name="feedbacksentiment"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("tags", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_feedback_guest_created", "guest_feedback", ["guest_id", "created_at"])
    op.create_table(
        "feedback_resolutions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("feedback_id", sa.Integer(), sa.ForeignKey("guest_feedback.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column(
            "status",
            sa.Enum(
                "open", "in_progress", "awaiting_guest", "resolved", "unable_to_resolve",
                name="resolutionstatus",
            ),
            nullable=False,
            index=True,
        ),
        sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_summary", sa.Text(), nullable=True),
        sa.Column("guest_notified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ----- JIT Access -----
    op.create_table(
        "jit_access_grants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column(
            "purpose",
            sa.Enum(
                "auditor", "contractor", "partner", "guest_collab", "emergency", "other",
                name="grantpurpose",
            ),
            nullable=False,
        ),
        sa.Column(
            "scope_kind",
            sa.Enum("read", "write", "approve", "export", name="grantscopekind"),
            nullable=False,
        ),
        sa.Column("resource_types", sa.JSON(), nullable=False),
        sa.Column("resource_filter", sa.JSON(), nullable=True),
        sa.Column("permissions", sa.JSON(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("active", "expired", "revoked", "consumed", name="grantstatus"),
            nullable=False,
            index=True,
        ),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("granted_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoke_after_use", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("revocation_reason", sa.String(255), nullable=True),
    )
    op.create_index("ix_jit_grant_user_status", "jit_access_grants", ["user_id", "status"])
    op.create_index("ix_jit_grant_expires", "jit_access_grants", ["expires_at"])
    op.create_table(
        "jit_access_activity",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("grant_id", sa.Integer(), sa.ForeignKey("jit_access_grants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=True),
        sa.Column("resource_id", sa.String(100), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ----- Corporate accounts -----
    op.create_table(
        "corporate_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False, index=True),
        sa.Column("legal_name", sa.String(255), nullable=True),
        sa.Column("tax_id", sa.String(100), nullable=True, index=True),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("website", sa.String(255), nullable=True),
        sa.Column("primary_contact_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("account_manager_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column(
            "status",
            sa.Enum("active", "prospect", "inactive", name="corporatestatus"),
            nullable=False,
        ),
        sa.Column("credit_limit", sa.Numeric(14, 2), nullable=True),
        sa.Column("payment_terms_days", sa.Integer(), nullable=True),
        sa.Column("discount_pct", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("rate_code", sa.String(50), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_corp_account_status", "corporate_accounts", ["status"])
    op.create_table(
        "corporate_memberships",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("corporate_id", sa.Integer(), sa.ForeignKey("corporate_accounts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("guest_id", sa.Integer(), sa.ForeignKey("guests.id"), nullable=False, index=True),
        sa.Column("role", sa.String(100), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("left_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ----- DSAR + Consent -----
    op.create_table(
        "dsar_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("subject_email", sa.String(255), nullable=False, index=True),
        sa.Column("subject_name", sa.String(255), nullable=True),
        sa.Column("guest_id", sa.Integer(), sa.ForeignKey("guests.id"), nullable=True, index=True),
        sa.Column(
            "kind",
            sa.Enum(
                "access", "export", "rectification", "erasure", "portability", "objection",
                name="dsarkind",
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "intake", "verifying_identity", "processing",
                "awaiting_delivery", "delivered", "rejected",
                name="dsarstatus",
            ),
            nullable=False,
            index=True,
        ),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("identity_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("identity_verified_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("delivery_method", sa.String(50), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("delivered_file_path", sa.String(500), nullable=True),
        sa.Column("delivered_file_sha256", sa.String(64), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
    )
    op.create_index("ix_dsar_status_received", "dsar_requests", ["status", "received_at"])

    op.create_table(
        "consent_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column(
            "kind",
            sa.Enum(
                "privacy_policy", "terms_of_service", "marketing_opt_in",
                "data_sharing", "cookies", "other",
                name="consentkind",
            ),
            nullable=False,
        ),
        sa.Column("version_label", sa.String(50), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("body_sha256", sa.String(64), nullable=False),
        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deprecated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("kind", "version_label", "tenant_id", name="uq_consent_version"),
    )
    op.create_table(
        "consent_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("consent_version_id", sa.Integer(), sa.ForeignKey("consent_versions.id"), nullable=False),
        sa.Column("guest_id", sa.Integer(), sa.ForeignKey("guests.id"), nullable=True, index=True),
        sa.Column("subject_email", sa.String(255), nullable=True, index=True),
        sa.Column("accepted", sa.Boolean(), nullable=False),
        sa.Column("method", sa.String(50), nullable=True),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_consent_record_guest", "consent_records", ["guest_id"])

    # ----- Allocation pool -----
    op.create_table(
        "room_allocations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("room_type_id", sa.Integer(), sa.ForeignKey("room_types.id"), nullable=False, index=True),
        sa.Column("night", sa.Date(), nullable=False),
        sa.Column("total_inventory", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("safety_stock", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("inbound", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("quarantine", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("room_type_id", "night", "tenant_id", name="uq_allocation_rt_night"),
    )
    op.create_index("ix_allocation_night", "room_allocations", ["night"])
    op.create_table(
        "channel_buffers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("room_type_id", sa.Integer(), sa.ForeignKey("room_types.id"), nullable=False, index=True),
        sa.Column("night", sa.Date(), nullable=False),
        sa.Column("channel", sa.String(50), nullable=False),
        sa.Column("max_sellable", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("room_type_id", "night", "channel", "tenant_id", name="uq_channel_buffer"),
    )
    op.create_table(
        "room_holds",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("room_type_id", sa.Integer(), sa.ForeignKey("room_types.id"), nullable=False, index=True),
        sa.Column("night_from", sa.Date(), nullable=False),
        sa.Column("night_to", sa.Date(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "reason",
            sa.Enum(
                "out_of_order", "housekeeping", "quarantine", "vip_hold",
                "safety_stock", "group_allocation",
                name="holdreason",
            ),
            nullable=False,
        ),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
    )
    op.create_index("ix_hold_room_type_window", "room_holds", ["room_type_id", "night_from", "night_to"])


def downgrade() -> None:
    for t in [
        "room_holds",
        "channel_buffers",
        "room_allocations",
        "consent_records",
        "consent_versions",
        "dsar_requests",
        "corporate_memberships",
        "corporate_accounts",
        "jit_access_activity",
        "jit_access_grants",
        "feedback_resolutions",
        "guest_feedback",
        "upsell_sends",
        "upsell_chain_runs",
        "upsell_steps",
        "upsell_chains",
        "anomaly_mutes",
        "anomaly_alerts",
        "kpi_baselines",
    ]:
        op.drop_table(t)
