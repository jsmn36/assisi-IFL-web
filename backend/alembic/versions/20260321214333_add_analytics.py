"""Add analytics tables

Revision ID: add_analytics
Revises: add_housekeeping
Create Date: 2024-01-15

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "add_analytics"
down_revision = "add_housekeeping"
branch_labels = None
depends_on = None


def upgrade():
    from sqlalchemy import inspect

    bind = op.get_bind()
    inspector = inspect(bind)
    existing = inspector.get_table_names()

    # Create daily_metrics table


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

    safe_drop_table("performance_kpis")
    safe_drop_index("ix_monthly_metrics_property_year_month", "monthly_metrics")
    safe_drop_index("ix_monthly_metrics_year_month", "monthly_metrics")
    safe_drop_table("monthly_metrics")
    safe_drop_index("ix_daily_metrics_property_date", "daily_metrics")
    safe_drop_index("ix_daily_metrics_business_date", "daily_metrics")
    safe_drop_table("daily_metrics")
