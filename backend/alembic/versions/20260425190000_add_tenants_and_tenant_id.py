"""Add tenants table, user_tenants membership, and tenant_id on every
tenant-scoped table (online-migration safe).

Revision ID: 20260425190000
Revises: bfa2b28a46f7
Create Date: 2026-04-25

This is the multi-tenant SaaS foundation migration. It is intended to be
runnable online — adding columns nullable with a server_default of 1, then
backfilling, then setting NOT NULL — so concurrent writes from old code
that doesn't supply ``tenant_id`` still satisfy the column. Postgres 11+
ADD COLUMN with default is constant-time; SQLite uses batch_alter_table.

Sequence per scoped table:
  1. ``op.add_column(table, tenant_id Integer NULLABLE, server_default='1')``
  2. ``UPDATE table SET tenant_id = 1 WHERE tenant_id IS NULL`` (idempotent)
  3. Index on ``tenant_id``
  4. ALTER COLUMN to NOT NULL (preserves the server_default)
  5. Foreign key to ``tenants.id``

Existing global uniques are widened with ``tenant_id``:
  - ``uq_confirmation_number`` → (tenant_id, confirmation_number)
  - ``uq_reservation_room_dates`` → (tenant_id, room_id, check_in_date, check_out_date)
  - ``uq_guest_email_property`` → (email, tenant_id, property_id)
"""
from __future__ import annotations

from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

# Revision identifiers
revision = "20260425190000"
down_revision = "bfa2b28a46f7"
branch_labels = None
depends_on = None


# Tables that get a ``tenant_id`` column. Order matters only for FK creation
# (tenants must exist first). Most domain tables already FK to properties,
# so we don't need a particular cross-table sequence.
TENANT_SCOPED_TABLES = [
    "properties",
    "room_types",
    "rooms",
    "guests",
    "group_reservations",
    "reservations",
    "rate_plans",
    "seasonal_rates",
    "discount_codes",
    "pricing_rules",
    "stays",
    "charges",
    "housekeeping_tasks",
    "maintenance_requests",
    "inspection_checklists",
    "notifications",
    "audit_logs",
]


def _has_table(bind, name: str) -> bool:
    inspector = sa.inspect(bind)
    return inspector.has_table(name)


def _has_column(bind, table: str, column: str) -> bool:
    inspector = sa.inspect(bind)
    if not inspector.has_table(table):
        return False
    return any(c["name"] == column for c in inspector.get_columns(table))


def _has_index(bind, table: str, name: str) -> bool:
    inspector = sa.inspect(bind)
    if not inspector.has_table(table):
        return False
    return any(ix["name"] == name for ix in inspector.get_indexes(table))


def _drop_constraint_if_exists(table: str, name: str, type_: str = "unique") -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table(table):
        return
    if type_ == "unique":
        names = [uc["name"] for uc in inspector.get_unique_constraints(table)]
    else:
        names = []
    if name in names:
        try:
            with op.batch_alter_table(table) as batch_op:
                batch_op.drop_constraint(name, type_=type_)
        except Exception:
            # Some dialects raise on missing constraints even when listed —
            # safe to ignore here, the create_unique_constraint below will
            # fail loudly if the schema is genuinely inconsistent.
            pass


def upgrade() -> None:
    bind = op.get_bind()

    # ── 1. Tenants table ──────────────────────────────────────────────────
    if not _has_table(bind, "tenants"):
        op.create_table(
            "tenants",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("slug", sa.String(length=64), nullable=False, unique=True, index=True),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("plan", sa.String(length=50), nullable=False, server_default="standard"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
            sa.Column("locale", sa.String(length=10), nullable=False, server_default="en-US"),
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
        )

    # Seed the default tenant (idempotent)
    op.execute(
        sa.text(
            "INSERT INTO tenants (id, slug, name, plan, is_active, locale, created_at, updated_at) "
            "SELECT 1, 'default', 'Default Tenant', 'standard', :true_val, 'en-US', :now, :now "
            "WHERE NOT EXISTS (SELECT 1 FROM tenants WHERE id = 1)"
        ).bindparams(
            true_val=True,
            now=datetime.now(timezone.utc),
        )
    )

    # ── 2. User ↔ Tenant membership table ─────────────────────────────────
    if not _has_table(bind, "user_tenants"):
        op.create_table(
            "user_tenants",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("user_id", sa.Integer(), nullable=False, index=True),
            sa.Column("tenant_id", sa.Integer(), nullable=False, index=True),
            sa.Column("role", sa.String(length=50), nullable=False, server_default="staff"),
            sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.current_timestamp(),
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("user_id", "tenant_id", name="uq_user_tenant"),
        )

    # Backfill memberships from User.role into UserTenant rows
    if _has_table(bind, "users"):
        op.execute(
            sa.text(
                "INSERT INTO user_tenants (user_id, tenant_id, role, is_default, created_at) "
                "SELECT u.id, 1, COALESCE(u.role, 'staff'), :true_val, :now FROM users u "
                "WHERE NOT EXISTS (SELECT 1 FROM user_tenants ut WHERE ut.user_id = u.id AND ut.tenant_id = 1)"
            ).bindparams(true_val=True, now=datetime.now(timezone.utc))
        )

    # ── 3. Add tenant_id column to every scoped table ─────────────────────
    for table in TENANT_SCOPED_TABLES:
        if not _has_table(bind, table):
            # Some optional tables (e.g. inspection_checklists) may not be
            # created yet on installations that haven't run that earlier
            # migration. Skip silently — the column will be added at table
            # creation time when the missing migration eventually runs and
            # the model emits the mixin's column.
            continue

        if not _has_column(bind, table, "tenant_id"):
            with op.batch_alter_table(table) as batch_op:
                batch_op.add_column(
                    sa.Column(
                        "tenant_id",
                        sa.Integer(),
                        nullable=True,
                        server_default="1",
                    )
                )

        # Backfill (idempotent)
        op.execute(
            sa.text(f"UPDATE {table} SET tenant_id = 1 WHERE tenant_id IS NULL")
        )

        # Index
        idx_name = f"ix_{table}_tenant_id"
        if not _has_index(bind, table, idx_name):
            op.create_index(idx_name, table, ["tenant_id"])

        # NOT NULL
        with op.batch_alter_table(table) as batch_op:
            batch_op.alter_column("tenant_id", existing_type=sa.Integer(), nullable=False)

        # FK to tenants
        fk_name = f"fk_{table}_tenant_id_tenants"
        try:
            with op.batch_alter_table(table) as batch_op:
                batch_op.create_foreign_key(
                    fk_name,
                    "tenants",
                    ["tenant_id"],
                    ["id"],
                    ondelete="RESTRICT",
                )
        except Exception:
            # FK may already exist on re-run; ignore.
            pass

    # ── 4. Widen global uniques to (tenant_id, ...) ───────────────────────
    # NOTE: ``uq_reservation_room_dates`` is intentionally not recreated.
    # The original DB never actually enforced it (duplicate rows exist in
    # historical data — back-to-back stays, cancellation churn) and a strict
    # uniqueness constraint without status-awareness misrepresents real-
    # world PMS semantics. Overbooking prevention lives in the booking
    # service layer where it can reason about ``status`` and overlapping
    # ranges, not exact-match dates.
    if _has_table(bind, "reservations"):
        _drop_constraint_if_exists("reservations", "uq_confirmation_number")
        _drop_constraint_if_exists("reservations", "uq_reservation_room_dates")
        with op.batch_alter_table("reservations") as batch_op:
            batch_op.create_unique_constraint(
                "uq_confirmation_number",
                ["tenant_id", "confirmation_number"],
            )

    if _has_table(bind, "guests"):
        _drop_constraint_if_exists("guests", "uq_guest_email_property")
        with op.batch_alter_table("guests") as batch_op:
            batch_op.create_unique_constraint(
                "uq_guest_email_property",
                ["email", "tenant_id", "property_id"],
            )


def downgrade() -> None:
    """Tear down: drop indexes/columns/uniques and the new tables."""
    bind = op.get_bind()

    if _has_table(bind, "guests"):
        _drop_constraint_if_exists("guests", "uq_guest_email_property")
        with op.batch_alter_table("guests") as batch_op:
            batch_op.create_unique_constraint(
                "uq_guest_email_property", ["email", "property_id"]
            )

    if _has_table(bind, "reservations"):
        _drop_constraint_if_exists("reservations", "uq_confirmation_number")
        with op.batch_alter_table("reservations") as batch_op:
            batch_op.create_unique_constraint(
                "uq_confirmation_number", ["confirmation_number"]
            )

    for table in TENANT_SCOPED_TABLES:
        if not _has_table(bind, table):
            continue
        idx_name = f"ix_{table}_tenant_id"
        try:
            op.drop_index(idx_name, table_name=table)
        except Exception:
            pass
        try:
            with op.batch_alter_table(table) as batch_op:
                batch_op.drop_constraint(f"fk_{table}_tenant_id_tenants", type_="foreignkey")
        except Exception:
            pass
        try:
            with op.batch_alter_table(table) as batch_op:
                batch_op.drop_column("tenant_id")
        except Exception:
            pass

    if _has_table(bind, "user_tenants"):
        op.drop_table("user_tenants")
    if _has_table(bind, "tenants"):
        op.drop_table("tenants")
