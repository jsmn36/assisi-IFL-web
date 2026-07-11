"""
Test CheckOutGate
"""
import pytest
from app.gates.check_out_gate import CheckOutGate
from app.models import (
    Property,
    RoomType,
    Room,
    Guest,
    Reservation,
    Stay,
    ReservationStatus,
    StayStatus,
)
from datetime import date, timedelta
from decimal import Decimal


@pytest.fixture
def setup_checkout_data(test_db):
    prop = Property(
        name="Test Hotel", code="TCO", city="NYC", state="NY", postal_code="10001"
    )
    test_db.add(prop)
    test_db.commit()

    room_type = RoomType(
        property_id=prop.id, code="STD", name="Standard", base_price=Decimal("100")
    )
    test_db.add(room_type)
    test_db.commit()

    room = Room(property_id=prop.id, room_type_id=room_type.id, room_number="202")
    test_db.add(room)
    test_db.commit()

    guest = Guest(first_name="Jane", last_name="Smith", email="jane@example.com")
    test_db.add(guest)
    test_db.commit()

    reservation = Reservation(
        property_id=prop.id,
        guest_id=guest.id,
        room_type_id=room_type.id,
        confirmation_number="CHO001",
        check_in_date=date.today() - timedelta(days=2),
        check_out_date=date.today(),
        number_of_nights=2,
        nightly_rate=Decimal("100"),
        total_amount=Decimal("200"),
        status=ReservationStatus.CHECKED_IN,
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
        status=StayStatus.CHECKED_IN,
    )
    test_db.add(stay)
    test_db.commit()

    return reservation, stay, room


def test_check_out_gate_pass(test_db, setup_checkout_data):
    """Gate passes when reservation and stay are checked in"""
    reservation, stay, room = setup_checkout_data
    result = CheckOutGate().execute({"reservation": reservation, "stay": stay})
    assert result.passed is True


def test_check_out_gate_fail_not_checked_in(test_db, setup_checkout_data):
    """Gate fails if reservation is not checked in"""
    reservation, stay, room = setup_checkout_data
    reservation.status = ReservationStatus.CONFIRMED
    result = CheckOutGate().execute({"reservation": reservation, "stay": stay})
    assert result.failed is True
    assert "not checked in" in result.message.lower()


def test_check_out_gate_fail_stay_not_checked_in(test_db, setup_checkout_data):
    """Gate fails if stay is not checked in"""
    reservation, stay, room = setup_checkout_data
    stay.status = StayStatus.RESERVED
    result = CheckOutGate().execute({"reservation": reservation, "stay": stay})
    assert result.failed is True
    assert "not checked in" in result.message.lower()


def test_check_out_gate_early_checkout_warning(test_db, setup_checkout_data):
    """Gate returns warning for early checkout"""
    reservation, stay, room = setup_checkout_data
    stay.check_out_date = date.today() + timedelta(days=3)
    test_db.flush()
    result = CheckOutGate().execute({"reservation": reservation, "stay": stay})
    assert result.passed is True
    assert result.is_warning is True
    assert "early" in result.message.lower()


def test_check_out_gate_fail_no_data(test_db):
    """Gate fails if no reservation or stay provided"""
    result = CheckOutGate().execute({"reservation": None, "stay": None})
    assert result.failed is True
