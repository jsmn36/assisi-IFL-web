import pytest
from datetime import date, timedelta
from decimal import Decimal

from app.models import (
    Property,
    RoomType,
    Guest,
    Reservation,
    ReservationStatus,
    StateTransitionHistory,
    Charge,
)
from app.state_machines import ReservationStateMachine


# --------------------------------------------------
# Fixture
# --------------------------------------------------
@pytest.fixture(scope="function")
def setup_reservation(test_db):
    """Create a reservation for state machine testing"""

    # Property
    property_obj = Property(
        name="Test",
        code="T",
        address_line1="123",
        city="C",
        state="S",
        postal_code="12345",
    )
    test_db.add(property_obj)
    test_db.commit()

    # Room Type
    room_type = RoomType(
        property_id=property_obj.id,
        code="STD",
        name="Standard",
        base_price=Decimal("100"),
    )
    test_db.add(room_type)
    test_db.commit()

    # Guest
    guest = Guest(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
    )
    test_db.add(guest)
    test_db.commit()

    # Reservation (default status should be PENDING)
    reservation = Reservation(
        property_id=property_obj.id,
        guest_id=guest.id,
        room_type_id=room_type.id,
        confirmation_number="SM001",
        check_in_date=date.today() + timedelta(days=7),
        check_out_date=date.today() + timedelta(days=10),
        number_of_nights=3,
        nightly_rate=Decimal("100"),
        total_amount=Decimal("300"),
        status=ReservationStatus.PENDING,
    )

    test_db.add(reservation)
    test_db.commit()
    test_db.refresh(reservation)

    return reservation


# --------------------------------------------------
# Tests
# --------------------------------------------------


def test_valid_transition_pending_to_confirmed(test_db, setup_reservation):
    """Valid transition: pending → confirmed"""
    reservation = setup_reservation
    sm = ReservationStateMachine(reservation, test_db)

    assert reservation.status == ReservationStatus.PENDING
    assert sm.can_transition_to(ReservationStatus.CONFIRMED)

    success, error = sm.transition_to(
        ReservationStatus.CONFIRMED,
        triggered_by="receptionist",
    )

    assert success is True
    assert error is None
    assert reservation.status == ReservationStatus.CONFIRMED

    history = (
        test_db.query(StateTransitionHistory)
        .filter_by(
            entity_type="reservation",
            entity_id=reservation.id,
        )
        .first()
    )

    assert history is not None
    assert history.from_state == "pending"
    assert history.to_state == "confirmed"
    assert history.is_successful is True


def test_invalid_transition_pending_to_checked_in(test_db, setup_reservation):
    """Invalid transition: pending → checked_in"""
    reservation = setup_reservation
    sm = ReservationStateMachine(reservation, test_db)

    success, error = sm.transition_to(
        ReservationStatus.CHECKED_IN,
        triggered_by="receptionist",
    )

    assert success is False
    assert error is not None
    assert "Invalid transition" in error
    assert reservation.status == ReservationStatus.PENDING

    history = (
        test_db.query(StateTransitionHistory)
        .filter_by(
            entity_type="reservation",
            entity_id=reservation.id,
            is_successful=False,
        )
        .first()
    )

    assert history is not None
    assert history.error_message is not None


def test_complete_lifecycle(test_db, setup_reservation):
    """pending → confirmed → checked_in → checked_out"""
    reservation = setup_reservation
    sm = ReservationStateMachine(reservation, test_db)

    assert sm.confirm("receptionist")[0]
    assert reservation.status == ReservationStatus.CONFIRMED

    assert sm.check_in("frontdesk")[0]
    assert reservation.status == ReservationStatus.CHECKED_IN

    assert sm.check_out("frontdesk")[0]
    assert reservation.status == ReservationStatus.CHECKED_OUT

    history_count = (
        test_db.query(StateTransitionHistory)
        .filter_by(
            entity_type="reservation",
            entity_id=reservation.id,
            is_successful=True,
        )
        .count()
    )

    assert history_count == 3


def test_cancellation_from_pending(test_db, setup_reservation):
    """Cancel from pending"""
    reservation = setup_reservation
    sm = ReservationStateMachine(reservation, test_db)

    success, _ = sm.cancel("guest", reason="Change of plans")

    assert success
    assert reservation.status == ReservationStatus.CANCELLED


def test_cancellation_from_confirmed(test_db, setup_reservation):
    """Cancel from confirmed"""
    reservation = setup_reservation
    sm = ReservationStateMachine(reservation, test_db)

    sm.confirm("receptionist")
    success, _ = sm.cancel("guest", reason="Emergency")

    assert success
    assert reservation.status == ReservationStatus.CANCELLED


def test_no_show_marking(test_db, setup_reservation):
    """Mark confirmed past reservation as no-show"""
    reservation = setup_reservation

    reservation.check_in_date = date.today() - timedelta(days=2)
    reservation.check_out_date = date.today() - timedelta(days=1)
    reservation.status = ReservationStatus.CONFIRMED
    test_db.commit()

    sm = ReservationStateMachine(reservation, test_db)

    success, _ = sm.mark_no_show("night_audit")

    assert success
    assert reservation.status == ReservationStatus.NO_SHOW


def test_cannot_mark_no_show_for_future_reservation(test_db, setup_reservation):
    """Future reservation cannot be marked no-show"""
    reservation = setup_reservation
    sm = ReservationStateMachine(reservation, test_db)

    sm.confirm("receptionist")

    success, error = sm.mark_no_show("system")

    assert not success
    assert "before check-in date" in error or "has not passed" in error
    assert reservation.status == ReservationStatus.CONFIRMED


def test_get_valid_transitions(test_db, setup_reservation):
    """Validate transition list"""
    reservation = setup_reservation
    sm = ReservationStateMachine(reservation, test_db)

    valid = sm.get_valid_transitions()
    assert ReservationStatus.CONFIRMED in valid
    assert ReservationStatus.CANCELLED in valid
    assert ReservationStatus.CHECKED_IN not in valid

    sm.confirm("receptionist")
    valid = sm.get_valid_transitions()
    assert ReservationStatus.CHECKED_IN in valid
    assert ReservationStatus.NO_SHOW in valid


def test_terminal_states_no_transitions(test_db, setup_reservation):
    """Terminal states should not allow transitions"""
    reservation = setup_reservation
    sm = ReservationStateMachine(reservation, test_db)

    sm.confirm("receptionist")
    sm.check_in("frontdesk")
    sm.check_out("frontdesk")

    valid = sm.get_valid_transitions()
    assert valid == []

    success, _ = sm.transition_to(ReservationStatus.PENDING)
    assert not success


def test_emergency_cancellation_after_check_in(test_db, setup_reservation):
    """Emergency cancel after check-in"""
    reservation = setup_reservation
    sm = ReservationStateMachine(reservation, test_db)

    sm.confirm("receptionist")
    sm.check_in("frontdesk")

    success, _ = sm.cancel("manager", reason="Emergency evacuation")

    assert success
    assert reservation.status == ReservationStatus.CANCELLED
