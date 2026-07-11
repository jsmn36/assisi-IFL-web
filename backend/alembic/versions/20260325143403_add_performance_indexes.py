"""Add performance indexes

Revision ID: add_performance_indexes
Revises: add_search
Create Date: 2024-01-21
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "add_performance_indexes"
down_revision = "add_compliance"
branch_labels = None
depends_on = None


def upgrade():
    # Reservation indexes
    try:
        op.create_index(
            "ix_reservations_check_in_date", "reservations", ["check_in_date"]
        )
    except Exception:
        pass
    try:
        op.create_index(
            "ix_reservations_check_out_date", "reservations", ["check_out_date"]
        )
    except Exception:
        pass
    try:
        op.create_index(
            "ix_reservations_status_check_in",
            "reservations",
            ["status", "check_in_date"],
        )
    except Exception:
        pass
    try:
        op.create_index("ix_reservations_guest_email", "reservations", ["guest_email"])
    except Exception:
        pass

    # Guest indexes
    try:
        op.create_index("ix_guests_email", "guests", ["email"])
    except Exception:
        pass
    try:
        op.create_index("ix_guests_phone", "guests", ["phone"])
    except Exception:
        pass
    try:
        op.create_index("ix_guests_name", "guests", ["last_name", "first_name"])
    except Exception:
        pass

    # Room indexes
    try:
        op.create_index("ix_rooms_status", "rooms", ["status"])
    except Exception:
        pass
    try:
        op.create_index("ix_rooms_type_status", "rooms", ["room_type", "status"])
    except Exception:
        pass

    # Charge indexes
    try:
        op.create_index("ix_charges_reservation_id", "charges", ["reservation_id"])
    except Exception:
        pass
    try:
        op.create_index("ix_charges_created_at", "charges", ["created_at"])
    except Exception:
        pass

    # Payment indexes
    try:
        op.create_index("ix_payments_reservation_id", "payments", ["reservation_id"])
    except Exception:
        pass
    try:
        op.create_index("ix_payments_status", "payments", ["status"])
    except Exception:
        pass

    # Housekeeping indexes
    try:
        op.create_index(
            "ix_housekeeping_tasks_room_id", "housekeeping_tasks", ["room_id"]
        )
    except Exception:
        pass
    try:
        op.create_index(
            "ix_housekeeping_tasks_status", "housekeeping_tasks", ["status"]
        )
    except Exception:
        pass
    try:
        op.create_index(
            "ix_housekeeping_tasks_assigned_date",
            "housekeeping_tasks",
            ["assigned_to", "scheduled_date"],
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

    safe_drop_index("ix_reservations_check_in_date", "reservations")
    safe_drop_index("ix_reservations_check_out_date", "reservations")
    safe_drop_index("ix_reservations_status", "reservations")
    safe_drop_index("ix_reservations_guest_id", "reservations")
    safe_drop_index("ix_reservations_room_id", "reservations")
    safe_drop_index("ix_guests_last_name", "guests")
    safe_drop_index("ix_guests_email", "guests")
    safe_drop_index("ix_rooms_room_number", "rooms")
    safe_drop_index("ix_rooms_status", "rooms")
    safe_drop_index("ix_rooms_room_type_id", "rooms")
