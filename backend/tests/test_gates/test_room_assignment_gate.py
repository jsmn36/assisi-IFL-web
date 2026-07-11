"""
Test RoomAssignmentGate
"""
import pytest
from app.gates.room_assignment_gate import RoomAssignmentGate
from app.models import (
    Property,
    RoomType,
    Room,
    Guest,
    Reservation,
    ReservationStatus,
    OccupancyState,
)
from datetime import date, timedelta
from decimal import Decimal


@pytest.fixture
def setup_assignment_data(test_db):
    prop = Property(
        name="Test Hotel", code="TRA", city="NYC", state="NY", postal_code="10001"
    )
    test_db.add(prop)
    test_db.commit()

    room_type = RoomType(
        property_id=prop.id,
        code="STD",
        name="Standard",
        base_price=Decimal("100"),
        max_occupancy=2,
    )
    test_db.add(room_type)
    test_db.commit()

    room = Room(property_id=prop.id, room_type_id=room_type.id, room_number="303")
    test_db.add(room)
    test_db.commit()

    guest = Guest(first_name="Bob", last_name="Jones", email="bob@example.com")
    test_db.add(guest)
    test_db.commit()

    reservation = Reservation(
        property_id=prop.id,
        guest_id=guest.id,
        room_type_id=room_type.id,
        confirmation_number="ASN001",
        check_in_date=date.today(),
        check_out_date=date.today() + timedelta(days=2),
        number_of_nights=2,
        nightly_rate=Decimal("100"),
        total_amount=Decimal("200"),
        num_adults=2,
        num_children=0,
        status=ReservationStatus.CONFIRMED,
    )
    test_db.add(reservation)
    test_db.commit()

    return reservation, room, room_type


def test_room_assignment_gate_pass(test_db, setup_assignment_data):
    """Gate passes when room is available and types match"""
    reservation, room, room_type = setup_assignment_data
    result = RoomAssignmentGate().execute({"reservation": reservation, "room": room})
    assert result.passed is True
    assert "can be assigned" in result.message.lower()


def test_room_assignment_gate_fail_room_occupied(test_db, setup_assignment_data):
    """Gate fails if room is occupied"""
    reservation, room, room_type = setup_assignment_data
    room.occupancy_state = OccupancyState.OCCUPIED
    test_db.commit()
    result = RoomAssignmentGate().execute({"reservation": reservation, "room": room})
    assert result.failed is True
    assert "not available" in result.message.lower()


def test_room_assignment_gate_fail_type_mismatch(
    test_db, setup_assignment_data, test_db_session=None
):
    """Gate fails if room type does not match reservation"""
    reservation, room, room_type = setup_assignment_data

    other_type = RoomType(
        property_id=room.property_id,
        code="STE",
        name="Suite",
        base_price=Decimal("300"),
        max_occupancy=4,
    )
    import pytest
    from sqlalchemy.orm import Session

    # just change the room's type_id to simulate mismatch
    room.room_type_id = room_type.id + 999
    result = RoomAssignmentGate().execute({"reservation": reservation, "room": room})
    assert result.failed is True


def test_room_assignment_gate_fail_capacity(test_db, setup_assignment_data):
    """Gate fails if too many guests for room capacity"""
    reservation, room, room_type = setup_assignment_data
    reservation.num_adults = 3  # exceeds max_occupancy of 2
    result = RoomAssignmentGate().execute({"reservation": reservation, "room": room})
    assert result.failed is True
    assert "capacity" in result.message.lower()


def test_room_assignment_gate_fail_no_data(test_db):
    """Gate fails if reservation or room is missing"""
    result = RoomAssignmentGate().execute({"reservation": None, "room": None})
    assert result.failed is True
