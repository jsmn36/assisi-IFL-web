"""Add notifications table

Revision ID: add_notifications
Revises: f4d2372225aa
Create Date: 2024-01-12
"""
from alembic import op
import sqlalchemy as sa

revision = "add_notifications"
down_revision = "f4d2372225aa"
branch_labels = None
depends_on = None


def upgrade():
    from sqlalchemy import inspect

    bind = op.get_bind()
    inspector = inspect(bind)
    existing = inspector.get_table_names()


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

    safe_drop_index("ix_notifications_status", "notifications")
    safe_drop_index("ix_notifications_reservation_id", "notifications")
    safe_drop_index("ix_notifications_guest_id", "notifications")
    safe_drop_table("notifications")
