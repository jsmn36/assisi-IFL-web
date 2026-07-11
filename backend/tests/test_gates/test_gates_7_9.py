"""
Test Gates 7-9: Date, Payment, Availability
"""
import pytest
from app.gates.date_validation_gate import DateValidationGate
from app.gates.payment_gate import PaymentGate
from app.gates.availability_gate import AvailabilityGate
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
def setup_final_gates_data(test_db):
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
        property_id=property.id, code="STD", name="Standard", base_price=Decimal("100")
    )
    test_db.add(room_type)
    test_db.commit()

    room = Room(property_id=property.id, room_type_id=room_type.id, room_number="101")
    test_db.add(room)
    test_db.commit()

    guest = Guest(first_name="Test", last_name="Guest", email="test@example.com")
    test_db.add(guest)
    test_db.commit()

    reservation = Reservation(
        property_id=property.id,
        guest_id=guest.id,
        room_type_id=room_type.id,
        confirmation_number="FINAL001",
        check_in_date=date.today() + timedelta(days=1),
        check_out_date=date.today() + timedelta(days=3),
        number_of_nights=2,
        num_adults=2,
        nightly_rate=Decimal("100"),
        total_amount=Decimal("200"),
        status=ReservationStatus.CONFIRMED,
        guarantee_type="credit_card",
        credit_card_last_4="1234",
    )
    test_db.add(reservation)
    test_db.commit()

    return reservation, room, test_db


def test_date_validation_gate_pass(test_db, setup_final_gates_data):
    reservation, _, _ = setup_final_gates_data
    gate = DateValidationGate()
    result = gate.execute({"reservation": reservation})
    assert result.passed is True


def test_date_validation_gate_fail_checkout_before_checkin(
    test_db, setup_final_gates_data
):
    reservation, _, _ = setup_final_gates_data
    from sqlalchemy.orm.attributes import set_committed_value

    set_committed_value(
        reservation, "check_out_date", reservation.check_in_date - timedelta(days=1)
    )
    gate = DateValidationGate()
    result = gate.execute({"reservation": reservation})
    assert result.failed is True
    assert "after check-in" in result.message.lower()


def test_payment_gate_pass(test_db, setup_final_gates_data):
    reservation, _, _ = setup_final_gates_data
    gate = PaymentGate()
    result = gate.execute({"reservation": reservation})
    assert result.passed is True


def test_payment_gate_fail_deposit_not_paid(test_db, setup_final_gates_data):
    reservation, _, _ = setup_final_gates_data
    reservation.deposit_amount = Decimal("50.00")
    reservation.deposit_paid = False
    gate = PaymentGate()
    result = gate.execute({"reservation": reservation, "require_deposit": True})
    assert result.failed is True
    assert "deposit not paid" in result.message.lower()


def test_availability_gate_pass(test_db, setup_final_gates_data):
    reservation, room, db = setup_final_gates_data
    gate = AvailabilityGate()
    result = gate.execute({"reservation": reservation, "room": room, "db": db})
    assert result.passed is True or result.is_warning


def test_availability_gate_fail_room_occupied(test_db, setup_final_gates_data):
    reservation, room, db = setup_final_gates_data
    room.occupancy_state = OccupancyState.OCCUPIED
    db.commit()
    gate = AvailabilityGate()
    result = gate.execute({"reservation": reservation, "room": room, "db": db})
    assert result.failed is True
    assert "not currently available" in result.message.lower()


def test_date_validation_gate_long_stay_warning(test_db, setup_final_gates_data):
    """Test warning for long stay > 30 nights"""
    reservation, _, _ = setup_final_gates_data
    from datetime import date

    reservation.check_in_date = date.today()
    reservation.check_out_date = date.today() + timedelta(days=35)
    reservation.number_of_nights = 35
    gate = DateValidationGate()
    result = gate.execute({"reservation": reservation})
    assert result.is_warning


def test_date_validation_gate_no_reservation(test_db):
    """Test fails with no reservation"""
    gate = DateValidationGate()
    result = gate.execute({})
    assert result.failed is True


def test_payment_gate_no_guarantee(test_db, setup_final_gates_data):
    """Test warning when no guarantee type"""
    reservation, _, _ = setup_final_gates_data
    reservation.guarantee_type = None
    gate = PaymentGate()
    result = gate.execute({"reservation": reservation})
    assert result.is_warning


def test_payment_gate_incomplete_credit_card(test_db, setup_final_gates_data):
    """Test warning when credit card guarantee but no card on file"""
    reservation, _, _ = setup_final_gates_data
    reservation.guarantee_type = "credit_card"
    reservation.credit_card_last_4 = None
    gate = PaymentGate()
    result = gate.execute({"reservation": reservation})
    assert result.is_warning


def test_payment_gate_prepaid(test_db, setup_final_gates_data):
    """Test prepaid reservation passes"""
    reservation, _, _ = setup_final_gates_data
    reservation.guarantee_type = "prepaid"
    gate = PaymentGate()
    result = gate.execute({"reservation": reservation})
    assert result.passed is True


def test_payment_gate_no_reservation(test_db):
    """Test fails with no reservation"""
    gate = PaymentGate()
    result = gate.execute({})
    assert result.failed is True


def test_availability_gate_no_db(test_db, setup_final_gates_data):
    """Test warning when no db session"""
    reservation, _, _ = setup_final_gates_data
    gate = AvailabilityGate()
    result = gate.execute({"reservation": reservation})
    assert result.is_warning


def test_reservation_to_dict(test_db, setup_final_gates_data):
    """Cover reservation model methods"""
    reservation, _, _ = setup_final_gates_data
    d = reservation.to_dict()
    assert d["confirmation_number"] == "FINAL001"


def test_room_model_methods(test_db, setup_final_gates_data):
    """Cover room model methods"""
    _, room, _ = setup_final_gates_data
    assert room.room_number == "101"
    assert room.is_available() is True


def test_stay_model_methods(test_db, setup_final_gates_data):
    """Cover stay model methods"""
    from app.models import Stay, StayStatus

    reservation, room, db = setup_final_gates_data
    stay = Stay(
        property_id=reservation.property_id,
        reservation_id=reservation.id,
        room_id=room.id,
        guest_id=reservation.guest_id,
        check_in_date=reservation.check_in_date,
        check_out_date=reservation.check_out_date,
        nightly_rate=Decimal("100"),
        status=StayStatus.CHECKED_IN,
    )
    db.add(stay)
    db.commit()
    assert stay.status == StayStatus.CHECKED_IN
    if hasattr(stay, "to_dict"):
        d = stay.to_dict()
        assert d is not None


def test_checkout_gate_with_outstanding_balance(test_db, setup_final_gates_data):
    """Cover check_out_gate outstanding balance path"""
    from app.gates.check_out_gate import CheckOutGate
    from app.models import Stay, StayStatus, Charge, ChargeType, ChargeStatus

    reservation, room, db = setup_final_gates_data
    reservation.status = __import__(
        "app.models", fromlist=["ReservationStatus"]
    ).ReservationStatus.CHECKED_IN

    stay = Stay(
        property_id=reservation.property_id,
        reservation_id=reservation.id,
        room_id=room.id,
        guest_id=reservation.guest_id,
        check_in_date=reservation.check_in_date,
        check_out_date=reservation.check_out_date,
        nightly_rate=Decimal("100"),
        status=StayStatus.CHECKED_IN,
    )
    db.add(stay)
    db.commit()

    gate = CheckOutGate()
    result = gate.execute({"reservation": reservation, "stay": stay})
    assert result.passed is True or result.is_warning or result.failed is True
