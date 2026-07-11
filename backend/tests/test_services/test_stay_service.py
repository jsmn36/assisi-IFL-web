"""
Test StayService
"""
import pytest
from app.services.stay_service import StayService
from app.services.reservation_service import ReservationService
from app.services.base_service import BusinessRuleError
from app.models import Property, RoomType, Room, Guest, StayStatus, ChargeType
from app.schemas import ReservationCreate
from datetime import date, timedelta
from decimal import Decimal


@pytest.fixture
def setup_stay_service_data(test_db):
    property = Property(
        name="Test",
        code="T",
        address_line1="123",
        city="C",
        state="S",
        postal_code="12345",
    )
    test_db.add(property)
    test_db.commit()

    room_type = RoomType(
        property_id=property.id,
        code="STD",
        name="Standard",
        base_price=Decimal("100"),
        max_occupancy=2,
        max_adults=2,
        max_children=1,
    )
    test_db.add(room_type)
    test_db.commit()

    room = Room(property_id=property.id, room_type_id=room_type.id, room_number="101")
    test_db.add(room)
    test_db.commit()

    guest = Guest(first_name="Jane", last_name="Doe", email="jane@example.com")
    test_db.add(guest)
    test_db.commit()

    # Create reservation using schema object (correct architecture)
    res_service = ReservationService(test_db)
    res_in = ReservationCreate(
        property_id=property.id,
        guest_id=guest.id,
        room_type_id=room_type.id,
        check_in_date=date.today(),
        check_out_date=date.today() + timedelta(days=2),
        num_adults=2,
        num_children=0,
    )
    reservation = res_service.create_reservation(res_in)
    res_service.confirm_reservation(reservation.id)

    return property, room, reservation


def test_create_stay(test_db, setup_stay_service_data):
    """Test creating a stay"""
    property, room, reservation = setup_stay_service_data

    service = StayService(test_db)
    stay = service.create_stay(
        reservation_id=reservation.id, room_id=room.id, created_by="frontdesk"
    )

    assert stay.id is not None
    assert stay.status == StayStatus.RESERVED
    assert stay.room_id == room.id


def test_check_in_stay(test_db, setup_stay_service_data):
    """Test checking in a stay"""
    property, room, reservation = setup_stay_service_data

    service = StayService(test_db)
    stay = service.create_stay(reservation.id, room.id)

    checked_in = service.check_in_stay(stay.id, "frontdesk")

    assert checked_in.status == StayStatus.CHECKED_IN
    assert checked_in.actual_check_in_time is not None
    assert checked_in.checked_in_by == "frontdesk"


def test_check_out_stay(test_db, setup_stay_service_data):
    """Test checking out a stay"""
    property, room, reservation = setup_stay_service_data

    service = StayService(test_db)
    stay = service.create_stay(reservation.id, room.id)
    service.check_in_stay(stay.id, "frontdesk")

    checked_out = service.check_out_stay(stay.id, "frontdesk", force_checkout=True)

    assert checked_out.status == StayStatus.CHECKED_OUT
    assert checked_out.actual_check_out_time is not None


def test_add_charge_to_stay(test_db, setup_stay_service_data):
    """Test adding charge to stay"""
    property, room, reservation = setup_stay_service_data

    service = StayService(test_db)
    stay = service.create_stay(reservation.id, room.id)

    charge = service.add_charge(
        stay_id=stay.id,
        charge_type=ChargeType.MINIBAR,
        description="Minibar items",
        amount=Decimal("25.00"),
        created_by="frontdesk",
    )

    assert charge.id is not None
    assert charge.charge_type == ChargeType.MINIBAR
    assert charge.total_amount == Decimal("25.00")


def test_post_room_charges(test_db, setup_stay_service_data):
    """Test posting room charges"""
    property, room, reservation = setup_stay_service_data

    service = StayService(test_db)
    stay = service.create_stay(reservation.id, room.id)

    charges = service.post_room_charges(stay.id, "night_audit")

    assert len(charges) == 2  # 2 nights
    assert all(c.charge_type == ChargeType.ROOM for c in charges)
