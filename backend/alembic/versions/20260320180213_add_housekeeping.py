"""Add housekeeping and maintenance tables

Revision ID: add_housekeeping
Revises: add_rate_management
Create Date: 2024-01-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "add_housekeeping"
down_revision = "add_rate_management"
branch_labels = None
depends_on = None


def upgrade():
    from sqlalchemy import inspect

    bind = op.get_bind()
    inspector = inspect(bind)
    existing = inspector.get_table_names()

    # Create users table


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

    safe_drop_column("rooms", "last_cleaned")
    safe_drop_table("housekeeping_staff")
    safe_drop_table("inspection_checklists")
    safe_drop_index("ix_maintenance_requests_priority", "maintenance_requests")
    safe_drop_index("ix_maintenance_requests_status", "maintenance_requests")
    safe_drop_table("maintenance_requests")
    safe_drop_index("ix_housekeeping_tasks_status", "housekeeping_tasks")
    safe_drop_index("ix_housekeeping_tasks_scheduled_date", "housekeeping_tasks")
    safe_drop_table("housekeeping_tasks")
    safe_drop_index("ix_users_email", "users")
    safe_drop_index("ix_users_username", "users")
    safe_drop_table("users")

    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP TYPE taskstatus")
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP TYPE tasktype")
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP TYPE taskpriority")
