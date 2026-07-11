"""
Day 4 Integration Test
Test state machines with complete booking workflow
"""
import pytest
from app.models import *
from app.state_machines import ReservationStateMachine, StayStateMachine
from datetime import date, datetime, timedelta
from decimal import Decimal


def test_complete_workflow_with_state_machines(test_db):
    """
    Integration test: Complete workflow using state machines
    """
    print("\n" + "=" * 60)
    print("DAY 4 INTEGRATION: STATE MACHINES IN ACTION")
    print("=" * 60)

    property = Property(
        name="State Machine Hotel",
        code="SM001",
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

    room = Room(property_id=property.id, room_type_id=room_type.id, room_number="301")
    test_db.add(room)
    test_db.commit()

    guest = Guest(first_name="Alice", last_name="Johnson", email="alice@example.com")
    test_db.add(guest)
    test_db.commit()

    reservation = Reservation(
        property_id=property.id,
        guest_id=guest.id,
        room_type_id=room_type.id,
        confirmation_number="SM-INT-001",
        check_in_date=date.today(),
        check_out_date=date.today() + timedelta(days=2),
        number_of_nights=2,
        nightly_rate=Decimal("100"),
        total_amount=Decimal("200"),
    )
    test_db.add(reservation)
    test_db.commit()
    test_db.refresh(reservation)

    assert reservation.status == ReservationStatus.PENDING

    res_sm = ReservationStateMachine(reservation, test_db)
    success, error = res_sm.confirm(confirmed_by="receptionist@hotel.com")
    assert success is True
    assert error is None

    history_count = (
        test_db.query(StateTransitionHistory)
        .filter_by(
            entity_type="reservation", entity_id=reservation.id, is_successful=True
        )
        .count()
    )
    assert history_count == 1

    success, error = res_sm.transition_to(
        ReservationStatus.CHECKED_OUT, triggered_by="hacker"
    )
    assert success is False
    assert error is not None
    test_db.refresh(reservation)
    assert reservation.status == ReservationStatus.CONFIRMED

    failed_history = (
        test_db.query(StateTransitionHistory)
        .filter_by(
            entity_type="reservation", entity_id=reservation.id, is_successful=False
        )
        .first()
    )
    assert failed_history is not None

    stay = Stay(
        property_id=property.id,
        reservation_id=reservation.id,
        guest_id=guest.id,
        room_id=room.id,
        check_in_date=reservation.check_in_date,
        check_out_date=reservation.check_out_date,
        nightly_rate=reservation.nightly_rate,
    )
    test_db.add(stay)
    test_db.commit()
    test_db.refresh(stay)
    assert stay.status == StayStatus.RESERVED

    success, _ = res_sm.check_in(checked_in_by="frontdesk@hotel.com")
    assert success is True

    stay_sm = StayStateMachine(stay, test_db)
    success, _ = stay_sm.check_in(checked_in_by="frontdesk@hotel.com")
    assert success is True
    test_db.refresh(room)
    assert room.occupancy_state == OccupancyState.OCCUPIED

    success, error = stay_sm.cancel(cancelled_by="guest")
    assert success is False

    reservation.status = ReservationStatus.CHECKED_IN
    test_db.commit()

    success, _ = stay_sm.check_out(checked_out_by="frontdesk@hotel.com")
    assert success is True

    res_sm = ReservationStateMachine(reservation, test_db)
    success, _ = res_sm.check_out(checked_out_by="frontdesk@hotel.com")
    assert success is True

    test_db.refresh(room)
    assert room.occupancy_state == OccupancyState.VACANT
    assert room.condition_state == ConditionState.DIRTY

    res_history = (
        test_db.query(StateTransitionHistory)
        .filter_by(
            entity_type="reservation", entity_id=reservation.id, is_successful=True
        )
        .all()
    )
    stay_history = (
        test_db.query(StateTransitionHistory)
        .filter_by(entity_type="stay", entity_id=stay.id, is_successful=True)
        .all()
    )
    failed = (
        test_db.query(StateTransitionHistory).filter_by(is_successful=False).count()
    )

    assert len(res_history) >= 3
    assert len(stay_history) >= 2
    assert failed >= 1


def test_no_show_scenario(test_db):
    """Test no-show scenario with state machine"""
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

    guest = Guest(first_name="Bob", last_name="NoShow", email="bob@example.com")
    test_db.add(guest)
    test_db.commit()

    reservation = Reservation(
        property_id=property.id,
        guest_id=guest.id,
        room_type_id=room_type.id,
        confirmation_number="NOSHOW001",
        check_in_date=date.today() - timedelta(days=2),
        check_out_date=date.today() - timedelta(days=1),
        number_of_nights=1,
        nightly_rate=Decimal("100"),
        total_amount=Decimal("100"),
        status=ReservationStatus.CONFIRMED,
    )
    test_db.add(reservation)
    test_db.commit()

    sm = ReservationStateMachine(reservation, test_db)
    success, error = sm.mark_no_show(marked_by="night_audit")
    assert success is True
    assert reservation.status == ReservationStatus.NO_SHOW


def test_concurrent_reservations_same_guest(test_db):
    """Test multiple reservations for same guest"""
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

    guest = Guest(
        first_name="Frequent", last_name="Traveler", email="frequent@example.com"
    )
    test_db.add(guest)
    test_db.commit()

    res1 = Reservation(
        property_id=property.id,
        guest_id=guest.id,
        room_type_id=room_type.id,
        confirmation_number="FREQ001",
        check_in_date=date.today(),
        check_out_date=date.today() + timedelta(days=2),
        number_of_nights=2,
        nightly_rate=Decimal("100"),
        total_amount=Decimal("200"),
    )
    res2 = Reservation(
        property_id=property.id,
        guest_id=guest.id,
        room_type_id=room_type.id,
        confirmation_number="FREQ002",
        check_in_date=date.today() + timedelta(days=30),
        check_out_date=date.today() + timedelta(days=33),
        number_of_nights=3,
        nightly_rate=Decimal("100"),
        total_amount=Decimal("300"),
    )
    test_db.add_all([res1, res2])
    test_db.commit()

    sm1 = ReservationStateMachine(res1, test_db)
    sm2 = ReservationStateMachine(res2, test_db)

    sm1.confirm(confirmed_by="receptionist")
    sm2.confirm(confirmed_by="receptionist")
    sm1.check_in(checked_in_by="frontdesk")

    assert res1.status == ReservationStatus.CHECKED_IN
    assert res2.status == ReservationStatus.CONFIRMED
