"""
Test CheckInService
"""
import pytest
from app.services.check_in_service import CheckInService
from app.services.reservation_service import ReservationService
from app.models import Property, RoomType, Room, Guest, ReservationStatus, StayStatus
from datetime import date, timedelta
from decimal import Decimal


@pytest.fixture
def setup_check_in_data(test_db):
    property = Property(
        name="Check-In Hotel",
        code="CHK",
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

    room = Room(
        property_id=property.id,
        room_type_id=room_type.id,
        room_number="201",
        occupancy_state="VACANT",
        condition_state="CLEAN",
        is_active=True,
        floor=2,
    )
    test_db.add(room)
    test_db.commit()

    guest = Guest(
        first_name="Alice",
        last_name="Check",
        email="alice@example.com",
        phone="+1-555-0100",
    )
    test_db.add(guest)
    test_db.commit()

    res_service = ReservationService(test_db)
    reservation = res_service.create_reservation(
        property_id=property.id,
        guest_id=guest.id,
        room_type_id=room_type.id,
        check_in_date=date.today(),
        check_out_date=date.today() + timedelta(days=3),
        num_adults=2,
        created_by="online",
    )
    res_service.confirm_reservation(reservation.id, "receptionist")
    # confirm_reservation is async — manually set status for sync test
    reservation.status = ReservationStatus.CONFIRMED
    test_db.flush()

    return property, room, reservation


def test_complete_check_in_workflow(test_db, setup_check_in_data):
    """Test complete check-in workflow"""
    property, room, reservation = setup_check_in_data

    service = CheckInService(test_db)

    result = service.check_in(
        reservation_id=reservation.id,
        room_id=room.id,
        checked_in_by="frontdesk",
        post_room_charges=True,
    )

    assert result["success"] is True
    assert result["reservation"].status == ReservationStatus.CHECKED_IN
    assert result["stay"].status == StayStatus.CHECKED_IN
    assert result["room"].room_number == "201"
    assert result["charges_posted"] == 3  # 3 nights
    assert "checked in" in result["message"].lower()


def test_check_in_auto_assign_room(test_db, setup_check_in_data):
    """Test check-in with auto room assignment"""
    property, room, reservation = setup_check_in_data
    service = CheckInService(test_db)

    result = service.check_in(
        confirmation_number=reservation.confirmation_number, checked_in_by="frontdesk"
    )

    assert result["success"] is True
    assert result["room"] is not None
    assert result["stay"].room_id == result["room"].id


def test_check_in_by_confirmation_number(test_db, setup_check_in_data):
    """Test check-in using confirmation number"""
    property, room, reservation = setup_check_in_data
    service = CheckInService(test_db)

    result = service.check_in(
        confirmation_number=reservation.confirmation_number,
        room_number="201",
        checked_in_by="frontdesk",
    )

    assert result["success"] is True
    assert result["reservation"].id == reservation.id
