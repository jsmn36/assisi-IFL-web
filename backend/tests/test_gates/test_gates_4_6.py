"""
Test Gates 4-6: Cancellation, Rate, Occupancy
"""
import pytest
from app.gates.reservation_cancellation_gate import ReservationCancellationGate
from app.gates.rate_validation_gate import RateValidationGate
from app.gates.occupancy_gate import OccupancyGate
from app.models import (
    Property,
    RoomType,
    Guest,
    Reservation,
    RatePlan,
    ReservationStatus,
)
from datetime import date, timedelta
from decimal import Decimal


@pytest.fixture
def setup_gates_data(test_db):
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
        max_occupancy=3,
        max_adults=2,
        max_children=2,
    )
    test_db.add(room_type)
    test_db.commit()

    guest = Guest(first_name="Test", last_name="Guest", email="test@example.com")
    test_db.add(guest)
    test_db.commit()

    rate_plan = RatePlan(
        property_id=property.id,
        room_type_id=room_type.id,
        code="BAR",
        name="Best Available Rate",
        base_rate=Decimal("100"),
        valid_from=date.today() - timedelta(days=30),
        valid_to=date.today() + timedelta(days=365),
        cancellation_policy="flexible",
    )
    test_db.add(rate_plan)
    test_db.commit()

    reservation = Reservation(
        property_id=property.id,
        guest_id=guest.id,
        room_type_id=room_type.id,
        confirmation_number="TEST001",
        check_in_date=date.today() + timedelta(days=7),
        check_out_date=date.today() + timedelta(days=9),
        number_of_nights=2,
        num_adults=2,
        num_children=0,
        nightly_rate=Decimal("100"),
        total_amount=Decimal("200"),
        status=ReservationStatus.CONFIRMED,
    )
    test_db.add(reservation)
    test_db.commit()

    return reservation, room_type, rate_plan


def test_cancellation_gate_pass(test_db, setup_gates_data):
    """Test cancellation gate passes for confirmed reservation"""
    reservation, _, _ = setup_gates_data

    gate = ReservationCancellationGate()
    result = gate.execute({"reservation": reservation})

    assert result.passed is True or result.status.value == "warning"


def test_cancellation_gate_fail_already_cancelled(test_db, setup_gates_data):
    """Test cancellation gate fails if already cancelled"""
    reservation, _, _ = setup_gates_data
    reservation.status = ReservationStatus.CANCELLED

    gate = ReservationCancellationGate()
    result = gate.execute({"reservation": reservation})

    assert result.failed is True
    assert "already cancelled" in result.message.lower()


def test_rate_validation_gate_pass(test_db, setup_gates_data):
    """Test rate validation gate passes with correct rates"""
    reservation, _, rate_plan = setup_gates_data

    gate = RateValidationGate()
    result = gate.execute({"reservation": reservation, "rate_plan": rate_plan})

    assert result.passed is True


def test_rate_validation_gate_fail_wrong_total(test_db, setup_gates_data):
    """Test rate validation fails with wrong total"""
    reservation, _, rate_plan = setup_gates_data
    reservation.total_amount = Decimal("999.99")  # Wrong!

    gate = RateValidationGate()
    result = gate.execute({"reservation": reservation, "rate_plan": rate_plan})

    assert result.failed is True
    assert "incorrect" in result.message.lower()


def test_occupancy_gate_pass(test_db, setup_gates_data):
    """Test occupancy gate passes with valid occupancy"""
    reservation, room_type, _ = setup_gates_data

    gate = OccupancyGate()
    result = gate.execute({"reservation": reservation, "room_type": room_type})

    assert result.passed is True


def test_occupancy_gate_fail_exceeds_max(test_db, setup_gates_data):
    """Test occupancy gate fails when exceeding max"""
    reservation, room_type, _ = setup_gates_data
    reservation.num_adults = 3
    reservation.num_children = 2  # Total: 5, max is 3

    gate = OccupancyGate()
    result = gate.execute({"reservation": reservation, "room_type": room_type})

    assert result.failed is True
    assert "exceeds" in result.message.lower()


def test_occupancy_gate_fail_no_adults(test_db, setup_gates_data):
    """Test occupancy gate fails with no adults"""
    reservation, room_type, _ = setup_gates_data
    reservation.num_adults = 0
    reservation.num_children = 2

    gate = OccupancyGate()
    result = gate.execute({"reservation": reservation, "room_type": room_type})

    assert result.failed is True
    assert "at least one adult" in result.message.lower()
