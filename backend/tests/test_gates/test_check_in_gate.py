"""
Test CheckInGate
"""
import pytest
from app.gates.check_in_gate import CheckInGate
from app.models import (
    Property,
    RoomType,
    Room,
    Guest,
    Reservation,
    Stay,
    ReservationStatus,
    OccupancyState,
)
from datetime import date, timedelta
from decimal import Decimal


@pytest.fixture
def setup_check_in_data(test_db):
    prop = Property(
        name="Test Hotel", code="TH", city="NYC", state="NY", postal_code="10001"
    )
    test_db.add(prop)
    test_db.commit()

    room_type = RoomType(
        property_id=prop.id, code="STD", name="Standard", base_price=Decimal("100")
    )
    test_db.add(room_type)
    test_db.commit()

    room = Room(property_id=prop.id, room_type_id=room_type.id, room_number="101")
    test_db.add(room)
    test_db.commit()

    guest = Guest(first_name="John", last_name="Doe", email="john@example.com")
    test_db.add(guest)
    test_db.commit()

    reservation = Reservation(
        property_id=prop.id,
        guest_id=guest.id,
        room_type_id=room_type.id,
        confirmation_number="CHK001",
        check_in_date=date.today(),
        check_out_date=date.today() + timedelta(days=2),
        number_of_nights=2,
        nightly_rate=Decimal("100"),
        total_amount=Decimal("200"),
        status=ReservationStatus.CONFIRMED,
    )
    test_db.add(reservation)
    test_db.commit()

    stay = Stay(
        property_id=prop.id,
        reservation_id=reservation.id,
        guest_id=guest.id,
        room_id=room.id,
        check_in_date=reservation.check_in_date,
        check_out_date=reservation.check_out_date,
        nightly_rate=reservation.nightly_rate,
    )
    test_db.add(stay)
    test_db.commit()

    return reservation, stay, room


def test_check_in_gate_pass(test_db, setup_check_in_data):
    """Gate passes with valid confirmed reservation and available room"""
    reservation, stay, room = setup_check_in_data
    result = CheckInGate().execute({"reservation": reservation, "stay": stay})
    assert result.passed is True
    assert "validated" in result.message.lower()


def test_check_in_gate_fail_not_confirmed(test_db, setup_check_in_data):
    """Gate fails if reservation is not confirmed"""
    reservation, stay, room = setup_check_in_data
    reservation.status = ReservationStatus.PENDING
    result = CheckInGate().execute({"reservation": reservation, "stay": stay})
    assert result.failed is True
    assert "confirmed" in result.message.lower()


def test_check_in_gate_fail_future_date(test_db, setup_check_in_data):
    """Gate fails if check-in date is in the future"""
    reservation, stay, room = setup_check_in_data
    reservation.check_in_date = date.today() + timedelta(days=7)
    result = CheckInGate().execute({"reservation": reservation, "stay": stay})
    assert result.failed is True
    assert "before reservation date" in result.message.lower()


def test_check_in_gate_fail_room_occupied(test_db, setup_check_in_data):
    """Gate fails if room is already occupied"""
    reservation, stay, room = setup_check_in_data
    room.occupancy_state = OccupancyState.OCCUPIED
    test_db.commit()
    result = CheckInGate().execute({"reservation": reservation, "stay": stay})
    assert result.failed is True
    assert "not available" in result.message.lower()


def test_check_in_gate_fail_no_reservation(test_db):
    """Gate fails if no reservation provided"""
    result = CheckInGate().execute({"reservation": None, "stay": None})
    assert result.failed is True
