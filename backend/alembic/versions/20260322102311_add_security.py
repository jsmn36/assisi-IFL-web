"""Add security features

Revision ID: add_security
Revises: add_analytics
Create Date: 2024-01-16

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "add_security"
down_revision = "add_analytics"
branch_labels = None
depends_on = None


def upgrade():
    from sqlalchemy import inspect

    bind = op.get_bind()
    inspector = inspect(bind)
    existing = inspector.get_table_names()

    def safe_add_column(table_name, column_def):
        try:
            if table_name in inspector.get_table_names():
                cols = [c["name"] for c in inspector.get_columns(table_name)]
                # Extract column name from the Column definition
                col_name = column_def.name
                if col_name not in cols:
                    op.add_column(table_name, column_def)
        except Exception as e:
            pass

    from sqlalchemy import inspect

    bind = op.get_bind()
    inspector = inspect(bind)
    existing = inspector.get_table_names()
    try:
        op.add_column(
            "users", sa.Column("first_name", sa.String(length=100), nullable=True)
        )
    except Exception:
        pass
    try:
        op.add_column(
            "users", sa.Column("last_name", sa.String(length=100), nullable=True)
        )
    except Exception:
        pass
    try:
        op.add_column("users", sa.Column("phone", sa.String(length=20), nullable=True))
    except Exception:
        pass
    try:
        op.add_column(
            "users",
            sa.Column(
                "is_superuser", sa.Boolean(), nullable=True, server_default="false"
            ),
        )
    except Exception:
        pass
    try:
        op.add_column(
            "users",
            sa.Column(
                "failed_login_attempts", sa.Integer(), nullable=True, server_default="0"
            ),
        )
    except Exception:
        pass
    try:
        op.add_column("users", sa.Column("locked_until", sa.DateTime(), nullable=True))
    except Exception:
        pass
    try:
        op.add_column("users", sa.Column("last_login", sa.DateTime(), nullable=True))
    except Exception:
        pass
    try:
        op.add_column(
            "users", sa.Column("last_password_change", sa.DateTime(), nullable=True)
        )
    except Exception:
        pass
    try:
        op.add_column(
            "users",
            sa.Column("password_reset_token", sa.String(length=200), nullable=True),
        )
    except Exception:
        pass
    try:
        op.add_column(
            "users", sa.Column("password_reset_expires", sa.DateTime(), nullable=True)
        )
    except Exception:
        pass
    try:
        op.add_column("users", sa.Column("updated_at", sa.DateTime(), nullable=True))
    except Exception:
        pass
    try:
        op.add_column(
            "users", sa.Column("created_by", sa.String(length=100), nullable=True)
        )
    except Exception:
        pass


def downgrade():
    from sqlalchemy import inspect

    bind = op.get_bind()
    inspector = inspect(bind)

    def safe_drop_index(index_name, table_name):
        try:
            indexes = [i["name"] for i in inspector.get_indexes(table_name)]
            if index_name in indexes:
                op.drop_index(index_name, table_name=table_name)
        except Exception:
            pass

    def safe_drop_table(table_name):
        try:
            if table_name in inspector.get_table_names():
                op.drop_table(table_name)
        except Exception:
            pass

    def safe_drop_column(table_name, column_name):
        try:
            cols = [c["name"] for c in inspector.get_columns(table_name)]
            if column_name in cols:
                op.drop_column(table_name, column_name)
        except Exception:
            pass

    safe_drop_index("ix_audit_logs_user_id", "audit_logs")
    safe_drop_index("ix_audit_logs_action", "audit_logs")
    safe_drop_index("ix_audit_logs_created_at", "audit_logs")
    safe_drop_table("audit_logs")
    safe_drop_index("ix_refresh_tokens_token", "refresh_tokens")
    safe_drop_table("refresh_tokens")
    safe_drop_column("users", "created_by")
    safe_drop_column("users", "updated_at")
    safe_drop_column("users", "password_reset_expires")
    safe_drop_column("users", "password_reset_token")
    safe_drop_column("users", "last_password_change")
    safe_drop_column("users", "last_login")
    safe_drop_column("users", "locked_until")
    safe_drop_column("users", "failed_login_attempts")
    safe_drop_column("users", "is_superuser")
    safe_drop_column("users", "phone")
    safe_drop_column("users", "last_name")
    safe_drop_column("users", "first_name")
