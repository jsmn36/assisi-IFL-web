"""Initial schema

Revision ID: 1574847754ef
Revises: 
Create Date: 2026-02-19 17:05:37.734620

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1574847754ef"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from sqlalchemy import inspect

    bind = op.get_bind()
    inspector = inspect(bind)
    existing = inspector.get_table_names()

    if "guests" not in existing:
        op.create_table(
            "guests",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("property_id", sa.Integer(), nullable=True),
            sa.Column("first_name", sa.String(length=100), nullable=False),
            sa.Column("last_name", sa.String(length=100), nullable=False),
            sa.Column("middle_name", sa.String(length=100), nullable=True),
            sa.Column("email", sa.String(length=255), nullable=True),
            sa.Column("phone", sa.String(length=20), nullable=True),
            sa.Column("mobile", sa.String(length=20), nullable=True),
            sa.Column("address_line1", sa.String(length=255), nullable=True),
            sa.Column("address_line2", sa.String(length=255), nullable=True),
            sa.Column("city", sa.String(length=100), nullable=True),
            sa.Column("state", sa.String(length=100), nullable=True),
            sa.Column("country", sa.String(length=100), nullable=True),
            sa.Column("postal_code", sa.String(length=20), nullable=True),
            sa.Column("passport_number", sa.String(length=50), nullable=True),
            sa.Column("drivers_license", sa.String(length=50), nullable=True),
            sa.Column("id_type", sa.String(length=50), nullable=True),
            sa.Column("id_number", sa.String(length=50), nullable=True),
            sa.Column("id_country", sa.String(length=100), nullable=True),
            sa.Column(
                "guest_type",
                sa.Enum("INDIVIDUAL", "CORPORATE", "GROUP", "VIP", name="guesttype"),
                nullable=False,
            ),
            sa.Column("company_name", sa.String(length=255), nullable=True),
            sa.Column("language", sa.String(length=10), nullable=True),
            sa.Column("nationality", sa.String(length=100), nullable=True),
            sa.Column("date_of_birth", sa.Date(), nullable=True),
            sa.Column("is_vip", sa.Boolean(), nullable=False),
            sa.Column("loyalty_number", sa.String(length=50), nullable=True),
            sa.Column("loyalty_tier", sa.String(length=50), nullable=True),
            sa.Column("special_requests", sa.String(length=500), nullable=True),
            sa.Column("dietary_restrictions", sa.String(length=500), nullable=True),
            sa.Column("accessibility_needs", sa.String(length=500), nullable=True),
            sa.Column("marketing_opt_in", sa.Boolean(), nullable=False),
            sa.Column("data_consent", sa.Boolean(), nullable=False),
            sa.Column("data_consent_date", sa.DateTime(), nullable=True),
            sa.Column("is_blacklisted", sa.Boolean(), nullable=False),
            sa.Column("blacklist_reason", sa.String(length=500), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("total_stays", sa.Integer(), nullable=False),
            sa.Column("total_nights", sa.Integer(), nullable=False),
            sa.Column("last_stay_date", sa.Date(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_guests_email"), "guests", ["email"], unique=False)
        op.create_index(
            op.f("ix_guests_first_name"), "guests", ["first_name"], unique=False
        )
        op.create_index(op.f("ix_guests_id"), "guests", ["id"], unique=False)
        op.create_index(
            op.f("ix_guests_last_name"), "guests", ["last_name"], unique=False
        )
        op.create_index(
            op.f("ix_guests_loyalty_number"), "guests", ["loyalty_number"], unique=False
        )
        op.create_index(
            op.f("ix_guests_property_id"), "guests", ["property_id"], unique=False
        )

    if "properties" not in existing:
        op.create_table(
            "properties",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("code", sa.String(length=50), nullable=False),
            sa.Column("address_line1", sa.String(length=255), nullable=False),
            sa.Column("address_line2", sa.String(length=255), nullable=True),
            sa.Column("city", sa.String(length=100), nullable=False),
            sa.Column("state", sa.String(length=100), nullable=True),
            sa.Column("country", sa.String(length=100), nullable=True),
            sa.Column("postal_code", sa.String(length=20), nullable=False),
            sa.Column("phone", sa.String(length=20), nullable=True),
            sa.Column("email", sa.String(length=255), nullable=True),
            sa.Column("timezone", sa.String(length=50), nullable=True),
            sa.Column("currency", sa.String(length=10), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_properties_code"), "properties", ["code"], unique=True)
        op.create_index(op.f("ix_properties_id"), "properties", ["id"], unique=False)

    if "room_types" not in existing:
        op.create_table(
            "room_types",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("code", sa.String(length=50), nullable=True),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("description", sa.String(length=255), nullable=True),
            sa.Column("base_price", sa.Float(), nullable=False),
            sa.Column("max_occupancy", sa.Integer(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_room_types_id"), "room_types", ["id"], unique=False)

    if "business_days" not in existing:
        op.create_table(
            "business_days",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("property_id", sa.Integer(), nullable=False),
            sa.Column("business_date", sa.Date(), nullable=False),
            sa.Column(
                "status",
                sa.Enum("OPEN", "CLOSED", "IN_AUDIT", "AUDIT_FAILED", name="daystatus"),
                nullable=False,
            ),
            sa.Column("day_opened_at", sa.DateTime(), nullable=True),
            sa.Column("day_opened_by", sa.String(length=100), nullable=True),
            sa.Column("day_closed_at", sa.DateTime(), nullable=True),
            sa.Column("day_closed_by", sa.String(length=100), nullable=True),
            sa.Column("night_audit_started_at", sa.DateTime(), nullable=True),
            sa.Column("night_audit_completed_at", sa.DateTime(), nullable=True),
            sa.Column("night_audit_run_by", sa.String(length=100), nullable=True),
            sa.Column("night_audit_status", sa.String(length=50), nullable=True),
            sa.Column("audit_check_1_result", sa.Boolean(), nullable=True),
            sa.Column("audit_check_2_result", sa.Boolean(), nullable=True),
            sa.Column("audit_check_3_result", sa.Boolean(), nullable=True),
            sa.Column("audit_check_4_result", sa.Boolean(), nullable=True),
            sa.Column("audit_check_5_result", sa.Boolean(), nullable=True),
            sa.Column("audit_check_6_result", sa.Boolean(), nullable=True),
            sa.Column("audit_check_7_result", sa.Boolean(), nullable=True),
            sa.Column("audit_check_8_result", sa.Boolean(), nullable=True),
            sa.Column("audit_error_log", sa.Text(), nullable=True),
            sa.Column(
                "total_revenue", sa.Numeric(precision=10, scale=2), nullable=True
            ),
            sa.Column("room_revenue", sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column(
                "total_charges", sa.Numeric(precision=10, scale=2), nullable=True
            ),
            sa.Column("total_occupancy", sa.Integer(), nullable=True),
            sa.Column("total_arrivals", sa.Integer(), nullable=True),
            sa.Column("total_departures", sa.Integer(), nullable=True),
            sa.Column("adr", sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column("rev_par", sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column(
                "occupancy_percent", sa.Numeric(precision=5, scale=2), nullable=True
            ),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(
                ["property_id"],
                ["properties.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_business_days_business_date"),
            "business_days",
            ["business_date"],
            unique=True,
        )
        op.create_index(
            op.f("ix_business_days_id"), "business_days", ["id"], unique=False
        )
        op.create_index(
            op.f("ix_business_days_property_id"),
            "business_days",
            ["property_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_business_days_status"), "business_days", ["status"], unique=False
        )

    if "reservations" not in existing:
        op.create_table(
            "reservations",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("property_id", sa.Integer(), nullable=False),
            sa.Column("guest_id", sa.Integer(), nullable=False),
            sa.Column("room_type_id", sa.Integer(), nullable=False),
            sa.Column("confirmation_number", sa.String(length=50), nullable=False),
            sa.Column("check_in_date", sa.Date(), nullable=False),
            sa.Column("check_out_date", sa.Date(), nullable=False),
            sa.Column("number_of_nights", sa.Integer(), nullable=False),
            sa.Column(
                "status",
                sa.Enum(
                    "PENDING",
                    "CONFIRMED",
                    "CHECKED_IN",
                    "CHECKED_OUT",
                    "CANCELLED",
                    "NO_SHOW",
                    name="reservationstatus",
                ),
                nullable=False,
            ),
            sa.Column(
                "source",
                sa.Enum(
                    "DIRECT",
                    "OTA",
                    "GDS",
                    "CORPORATE",
                    "GROUP",
                    "LOYALTY",
                    name="reservationsource",
                ),
                nullable=False,
            ),
            sa.Column("num_adults", sa.Integer(), nullable=False),
            sa.Column("num_children", sa.Integer(), nullable=False),
            sa.Column(
                "total_amount", sa.Numeric(precision=10, scale=2), nullable=False
            ),
            sa.Column(
                "deposit_amount", sa.Numeric(precision=10, scale=2), nullable=True
            ),
            sa.Column("deposit_paid", sa.Boolean(), nullable=False),
            sa.Column(
                "nightly_rate", sa.Numeric(precision=10, scale=2), nullable=False
            ),
            sa.Column("rate_code", sa.String(length=50), nullable=True),
            sa.Column("special_requests", sa.Text(), nullable=True),
            sa.Column("internal_notes", sa.Text(), nullable=True),
            sa.Column("is_cancelled", sa.Boolean(), nullable=False),
            sa.Column("cancelled_at", sa.DateTime(), nullable=True),
            sa.Column("cancelled_by", sa.String(length=100), nullable=True),
            sa.Column("cancellation_reason", sa.String(length=500), nullable=True),
            sa.Column(
                "cancellation_fee", sa.Numeric(precision=10, scale=2), nullable=True
            ),
            sa.Column("guarantee_type", sa.String(length=50), nullable=True),
            sa.Column("credit_card_last_4", sa.String(length=4), nullable=True),
            sa.Column("estimated_arrival_time", sa.String(length=10), nullable=True),
            sa.Column("actual_arrival_time", sa.DateTime(), nullable=True),
            sa.Column("status_changed_at", sa.DateTime(), nullable=True),
            sa.Column("confirmed_at", sa.DateTime(), nullable=True),
            sa.Column("confirmed_by", sa.String(length=100), nullable=True),
            sa.Column("promo_code", sa.String(length=50), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("created_by", sa.String(length=100), nullable=True),
            sa.ForeignKeyConstraint(
                ["guest_id"],
                ["guests.id"],
            ),
            sa.ForeignKeyConstraint(
                ["property_id"],
                ["properties.id"],
            ),
            sa.ForeignKeyConstraint(
                ["room_type_id"],
                ["room_types.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_reservations_check_in_date"),
            "reservations",
            ["check_in_date"],
            unique=False,
        )
        op.create_index(
            op.f("ix_reservations_check_out_date"),
            "reservations",
            ["check_out_date"],
            unique=False,
        )
        op.create_index(
            op.f("ix_reservations_confirmation_number"),
            "reservations",
            ["confirmation_number"],
            unique=True,
        )
        op.create_index(
            op.f("ix_reservations_created_at"),
            "reservations",
            ["created_at"],
            unique=False,
        )
        op.create_index(
            op.f("ix_reservations_guest_id"), "reservations", ["guest_id"], unique=False
        )
        op.create_index(
            op.f("ix_reservations_id"), "reservations", ["id"], unique=False
        )
        op.create_index(
            op.f("ix_reservations_is_cancelled"),
            "reservations",
            ["is_cancelled"],
            unique=False,
        )
        op.create_index(
            op.f("ix_reservations_property_id"),
            "reservations",
            ["property_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_reservations_room_type_id"),
            "reservations",
            ["room_type_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_reservations_status"), "reservations", ["status"], unique=False
        )

    if "rooms" not in existing:
        op.create_table(
            "rooms",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("property_id", sa.Integer(), nullable=False),
            sa.Column("number", sa.String(length=20), nullable=False),
            sa.Column("floor", sa.Integer(), nullable=True),
            sa.Column(
                "occupancy_state",
                sa.Enum("VACANT", "OCCUPIED", "OUT_OF_ORDER", name="occupancystate"),
                nullable=False,
            ),
            sa.Column(
                "condition_state",
                sa.Enum("CLEAN", "DIRTY", "INSPECTED", name="conditionstate"),
                nullable=False,
            ),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(
                ["property_id"],
                ["properties.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_rooms_id"), "rooms", ["id"], unique=False)

    if "stays" not in existing:
        op.create_table(
            "stays",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("property_id", sa.Integer(), nullable=False),
            sa.Column("reservation_id", sa.Integer(), nullable=False),
            sa.Column("guest_id", sa.Integer(), nullable=False),
            sa.Column("room_id", sa.Integer(), nullable=False),
            sa.Column("check_in_date", sa.Date(), nullable=False),
            sa.Column("check_out_date", sa.Date(), nullable=False),
            sa.Column("actual_check_in_time", sa.DateTime(), nullable=True),
            sa.Column("actual_check_out_time", sa.DateTime(), nullable=True),
            sa.Column(
                "status",
                sa.Enum(
                    "RESERVED",
                    "CHECKED_IN",
                    "CHECKED_OUT",
                    "CANCELLED",
                    name="staystatus",
                ),
                nullable=False,
            ),
            sa.Column("num_adults", sa.Integer(), nullable=False),
            sa.Column("num_children", sa.Integer(), nullable=False),
            sa.Column(
                "total_room_charges", sa.Numeric(precision=10, scale=2), nullable=False
            ),
            sa.Column(
                "total_other_charges", sa.Numeric(precision=10, scale=2), nullable=False
            ),
            sa.Column(
                "total_charges", sa.Numeric(precision=10, scale=2), nullable=False
            ),
            sa.Column(
                "nightly_rate", sa.Numeric(precision=10, scale=2), nullable=False
            ),
            sa.Column("is_walk_in", sa.Boolean(), nullable=False),
            sa.Column("is_early_checkin", sa.Boolean(), nullable=False),
            sa.Column("is_late_checkout", sa.Boolean(), nullable=False),
            sa.Column("is_day_use", sa.Boolean(), nullable=False),
            sa.Column("requires_cleaning", sa.Boolean(), nullable=False),
            sa.Column("cleaning_completed", sa.Boolean(), nullable=False),
            sa.Column("checked_in_by", sa.String(length=100), nullable=True),
            sa.Column("checked_out_by", sa.String(length=100), nullable=True),
            sa.Column("stay_notes", sa.String(length=1000), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(
                ["guest_id"],
                ["guests.id"],
            ),
            sa.ForeignKeyConstraint(
                ["property_id"],
                ["properties.id"],
            ),
            sa.ForeignKeyConstraint(
                ["reservation_id"],
                ["reservations.id"],
            ),
            sa.ForeignKeyConstraint(
                ["room_id"],
                ["rooms.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_stays_check_in_date"), "stays", ["check_in_date"], unique=False
        )
        op.create_index(
            op.f("ix_stays_check_out_date"), "stays", ["check_out_date"], unique=False
        )
        op.create_index(op.f("ix_stays_guest_id"), "stays", ["guest_id"], unique=False)
        op.create_index(op.f("ix_stays_id"), "stays", ["id"], unique=False)
        op.create_index(
            op.f("ix_stays_property_id"), "stays", ["property_id"], unique=False
        )
        op.create_index(
            op.f("ix_stays_reservation_id"), "stays", ["reservation_id"], unique=False
        )
        op.create_index(op.f("ix_stays_room_id"), "stays", ["room_id"], unique=False)
        op.create_index(op.f("ix_stays_status"), "stays", ["status"], unique=False)
        # ### end Alembic commands ###


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

    # Drop all indexes safely
    for tname in ["stays", "reservations", "guests", "rooms", "properties"]:
        try:
            for idx_info in inspector.get_indexes(tname):
                safe_drop_index(idx_info["name"], tname)
        except Exception:
            pass

    # Drop tables in dependency order
    safe_drop_table("stays")
    safe_drop_table("reservations")
    safe_drop_table("guests")
    safe_drop_table("rooms")
    safe_drop_table("properties")
