"""Add compliance and audit tables

Revision ID: add_compliance
Revises: add_security
Create Date: 2024-01-18

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "add_compliance"
down_revision = "add_security"
branch_labels = None
depends_on = None


def upgrade():
    from sqlalchemy import inspect

    bind = op.get_bind()
    inspector = inspect(bind)
    existing = inspector.get_table_names()

    # Create compliance_logs table


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

    safe_drop_index("ix_data_retention_policies_data_type", "data_retention_policies")
    safe_drop_table("data_retention_policies")

    safe_drop_index("ix_data_access_logs_resource", "data_access_logs")
    safe_drop_index("ix_data_access_logs_created_at", "data_access_logs")
    safe_drop_table("data_access_logs")

    safe_drop_index("ix_compliance_logs_status", "compliance_logs")
    safe_drop_index("ix_compliance_logs_type", "compliance_logs")
    safe_drop_index("ix_compliance_logs_created_at", "compliance_logs")
    safe_drop_table("compliance_logs")
