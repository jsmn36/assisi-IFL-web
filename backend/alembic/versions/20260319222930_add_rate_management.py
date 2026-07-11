"""Add rate management tables

Revision ID: add_rate_management
Revises: add_notifications
Create Date: 2024-01-13

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "add_rate_management"
down_revision = "add_notifications"
branch_labels = None
depends_on = None


def upgrade():
    from sqlalchemy import inspect

    bind = op.get_bind()
    inspector = inspect(bind)
    existing = inspector.get_table_names()

    # Create rate_plans table


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

    safe_drop_table("pricing_rules")
    safe_drop_index("ix_discount_codes_code", "discount_codes")
    safe_drop_table("discount_codes")
    safe_drop_table("seasonal_rates")
    safe_drop_index("ix_rate_plans_code", "rate_plans")
    safe_drop_table("rate_plans")

    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP TYPE seasontype")
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP TYPE rateplantype")
