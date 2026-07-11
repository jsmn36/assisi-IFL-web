"""Add notification preferences

Revision ID: add_notification_preferences
Revises: add_task_history
Create Date: 2024-01-24

"""
from alembic import op
import sqlalchemy as sa

revision = "add_notification_preferences"
down_revision = "add_task_history"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "notification_preferences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "reservation_confirmation", sa.Boolean(), server_default=sa.text("true")
        ),
        sa.Column("reservation_reminder", sa.Boolean(), server_default=sa.text("true")),
        sa.Column(
            "reservation_cancellation", sa.Boolean(), server_default=sa.text("true")
        ),
        sa.Column("payment_received", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("payment_failed", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("payment_reminder", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("account_updates", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("security_alerts", sa.Boolean(), server_default=sa.text("true")),
        sa.Column(
            "system_announcements", sa.Boolean(), server_default=sa.text("false")
        ),
        sa.Column("promotional_emails", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("newsletter", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("daily_reports", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("weekly_reports", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("monthly_reports", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("email_enabled", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("sms_enabled", sa.Boolean(), server_default=sa.text("false")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_notification_preferences_user_id",
        "notification_preferences",
        ["user_id"],
        unique=True,
    )


def downgrade():
    op.drop_index(
        "ix_notification_preferences_user_id", table_name="notification_preferences"
    )
    op.drop_table("notification_preferences")
