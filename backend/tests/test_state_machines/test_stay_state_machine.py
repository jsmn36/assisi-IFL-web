import pytest
from datetime import date, timedelta
from decimal import Decimal

from app.models import (
    Property,
    RoomType,
    Room,
    Guest,
    Reservation,
    Stay,
    StayStatus,
    OccupancyState,
    ConditionState,
    ReservationStatus,
    StateTransitionHistory,
)
from app.state_machines import StayStateMachine


@pytest.fixture
def setup_stay(test_db):
    """Create a stay for testing"""

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
    )
    test_db.add(room_type)
    test_db.commit()

    room = Room(
        property_id=property.id,
        room_type_id=room_type.id,
        room_number="101",
    )
    test_db.add(room)
    test_db.commit()

    guest = Guest(
        first_name="Jane",
        last_name="Smith",
        email="jane@example.com",
    )
    test_db.add(guest)
    test_db.commit()

    reservation = Reservation(
        property_id=property.id,
        guest_id=guest.id,
        room_type_id=room_type.id,
        confirmation_number="STAY001",
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
        property_id=property.id,
        reservation_id=reservation.id,
        guest_id=guest.id,
        room_id=room.id,
        check_in_date=date.today(),
        check_out_date=date.today() + timedelta(days=2),
        nightly_rate=Decimal("100"),
    )
    test_db.add(stay)
    test_db.commit()
    test_db.refresh(stay)

    return stay


def test_valid_transition_reserved_to_checked_in(test_db, setup_stay):
    """Test valid transition: reserved → checked_in"""
    stay = setup_stay
    sm = StayStateMachine(stay, test_db)

    assert stay.status == StayStatus.RESERVED
    assert sm.can_transition_to(StayStatus.CHECKED_IN) is True

    success, error = sm.check_in(checked_in_by="frontdesk")

    assert success is True
    assert error is None
    assert stay.status == StayStatus.CHECKED_IN
    assert stay.actual_check_in_time is not None

    test_db.refresh(stay.room)
    assert stay.room.occupancy_state == OccupancyState.OCCUPIED

    history = (
        test_db.query(StateTransitionHistory)
        .filter_by(entity_type="stay", entity_id=stay.id)
        .first()
    )

    assert history is not None
    assert history.from_state == "reserved"
    assert history.to_state == "checked_in"
    assert history.is_successful is True


def test_invalid_transition_reserved_to_checked_out(test_db, setup_stay):
    """Test invalid transition: reserved → checked_out"""
    stay = setup_stay
    sm = StayStateMachine(stay, test_db)

    success, error = sm.check_out(checked_out_by="frontdesk")

    assert success is False
    assert error is not None
    assert "Invalid transition" in error
    assert stay.status == StayStatus.RESERVED


def test_complete_lifecycle(test_db, setup_stay):
    """Test complete lifecycle: reserved → checked_in → checked_out"""
    stay = setup_stay
    sm = StayStateMachine(stay, test_db)

    success, _ = sm.check_in(checked_in_by="frontdesk")
    assert success is True
    assert stay.status == StayStatus.CHECKED_IN

    success, _ = sm.check_out(checked_out_by="frontdesk")
    assert success is True
    assert stay.status == StayStatus.CHECKED_OUT
    assert stay.actual_check_out_time is not None
    assert stay.requires_cleaning is True

    test_db.refresh(stay.room)
    assert stay.room.occupancy_state == OccupancyState.VACANT
    assert stay.room.condition_state == ConditionState.DIRTY

    history_count = (
        test_db.query(StateTransitionHistory)
        .filter_by(
            entity_type="stay",
            entity_id=stay.id,
            is_successful=True,
        )
        .count()
    )

    assert history_count == 2


def test_cancellation_before_check_in(test_db, setup_stay):
    """Test cancellation before check-in"""
    stay = setup_stay
    sm = StayStateMachine(stay, test_db)

    success, _ = sm.cancel(cancelled_by="guest", reason="Change of plans")

    assert success is True
    assert stay.status == StayStatus.CANCELLED


def test_cannot_cancel_after_check_in(test_db, setup_stay):
    """Test that cannot cancel after checked in"""
    stay = setup_stay
    sm = StayStateMachine(stay, test_db)

    sm.check_in(checked_in_by="frontdesk")

    success, error = sm.cancel(cancelled_by="guest")

    assert success is False
    assert "Invalid transition" in error
    assert stay.status == StayStatus.CHECKED_IN


def test_get_valid_transitions(test_db, setup_stay):
    """Test getting list of valid transitions"""
    stay = setup_stay
    sm = StayStateMachine(stay, test_db)

    valid = sm.get_valid_transitions()
    assert StayStatus.CHECKED_IN in valid
    assert StayStatus.CANCELLED in valid
    assert StayStatus.CHECKED_OUT not in valid

    sm.check_in(checked_in_by="frontdesk")
    valid = sm.get_valid_transitions()
    assert StayStatus.CHECKED_OUT in valid
    assert StayStatus.CANCELLED not in valid


def test_terminal_states_no_transitions(test_db, setup_stay):
    """Test that terminal states have no valid transitions"""
    stay = setup_stay
    sm = StayStateMachine(stay, test_db)

    sm.check_in(checked_in_by="frontdesk")
    sm.check_out(checked_out_by="frontdesk")

    valid = sm.get_valid_transitions()
    assert len(valid) == 0

    success, _ = sm.transition_to(
        StayStatus.RESERVED,
        triggered_by="system",
    )
    assert success is False


def test_room_status_updates_on_check_in(test_db, setup_stay):
    """Test that room status updates when checking in"""
    stay = setup_stay
    sm = StayStateMachine(stay, test_db)

    assert stay.room.occupancy_state == OccupancyState.VACANT

    sm.check_in(checked_in_by="frontdesk")

    test_db.refresh(stay.room)
    assert stay.room.occupancy_state == OccupancyState.OCCUPIED
    assert stay.room.occupancy_changed_at is not None


def test_room_status_updates_on_check_out(test_db, setup_stay):
    """Test that room status updates when checking out"""
    stay = setup_stay
    sm = StayStateMachine(stay, test_db)

    sm.check_in(checked_in_by="frontdesk")
    test_db.refresh(stay.room)
    assert stay.room.occupancy_state == OccupancyState.OCCUPIED

    sm.check_out(checked_out_by="frontdesk")

    test_db.refresh(stay.room)
    assert stay.room.occupancy_state == OccupancyState.VACANT
    assert stay.room.condition_state == ConditionState.DIRTY
    assert stay.requires_cleaning is True


def test_inactive_room_prevents_check_in(test_db, setup_stay):
    """Test that cannot check into inactive room"""
    stay = setup_stay
    sm = StayStateMachine(stay, test_db)

    stay.room.is_active = False
    test_db.commit()

    success, error = sm.check_in(checked_in_by="frontdesk")

    assert success is False
    assert "not active" in error
    assert stay.status == StayStatus.RESERVED
