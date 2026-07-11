"""Add search and filter tables

Revision ID: add_search
Revises: add_compliance
Create Date: 2024-01-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers
revision = "add_search"
down_revision = "add_compliance"
branch_labels = None
depends_on = None


def upgrade():
    from sqlalchemy import inspect

    bind = op.get_bind()
    inspector = inspect(bind)
    existing = inspector.get_table_names()

    # Create saved_searches table


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

    safe_drop_index("ix_quick_filters_is_active", "quick_filters")
    safe_drop_index("ix_quick_filters_entity_type", "quick_filters")
    safe_drop_table("quick_filters")
    safe_drop_index("ix_search_history_entity_type", "search_history")
    safe_drop_index("ix_search_history_created_at", "search_history")
    safe_drop_index("ix_search_history_user_id", "search_history")
    safe_drop_table("search_history")
    safe_drop_index("ix_saved_searches_entity_type", "saved_searches")
    safe_drop_index("ix_saved_searches_user_id", "saved_searches")
    safe_drop_table("saved_searches")
