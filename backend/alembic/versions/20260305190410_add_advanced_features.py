"""Add advanced features: GroupReservation

Revision ID: add_advanced_features
Revises: 2a05cdeeb5da
Create Date: 2026-03-05
"""
from alembic import op
import sqlalchemy as sa

revision = "add_advanced_features"
down_revision = "2a05cdeeb5da"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from sqlalchemy import inspect

    bind = op.get_bind()
    inspector = inspect(bind)
    existing = inspector.get_table_names()

    # -- group_reservations --------------------------------------------------


def downgrade() -> None:
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

    try:
        with op.batch_alter_table("reservations") as batch_op:
            batch_op.drop_constraint(
                "fk_reservations_group_reservation", type_="foreignkey"
            )
            batch_op.drop_column("group_reservation_id")
    except Exception:
        pass

    safe_drop_index("ix_group_reservations_group_code", "group_reservations")
    safe_drop_table("group_reservations")
