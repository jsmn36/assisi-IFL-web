import pytest
from datetime import date, timedelta
from decimal import Decimal

from app.models import (
    Property,
    RoomType,
    Room,
    Guest,
    RatePlan,
    Reservation,
    Stay,
    ReservationStatus,
    GateExecutionHistory,
)
from app.models.stay import StayStatus
from app.models.room import OccupancyState, ConditionState
from app.gates import (
    GateExecutor,
    GateStatus,
    DateValidationGate,
    OccupancyGate,
    RateValidationGate,
    PaymentGate,
    AvailabilityGate,
    RoomAssignmentGate,
    CheckInGate,
    CheckOutGate,
    ReservationCancellationGate,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_property(db, name="Test Hotel", code="TST001"):
    p = Property(
        name=name,
        code=code,
        address_line1="123 Main St",
        city="City",
        state="ST",
        postal_code="12345",
    )
    db.add(p)
    db.commit()
    return p


def make_room_type(
    db,
    property_id,
    code="DLX",
    base_price=Decimal("150"),
    max_occupancy=3,
    max_adults=2,
    max_children=2,
):
    rt = RoomType(
        property_id=property_id,
        code=code,
        name="Deluxe",
        base_price=base_price,
        max_occupancy=max_occupancy,
        max_adults=max_adults,
        max_children=max_children,
    )
    db.add(rt)
    db.commit()
    return rt


def make_room(db, property_id, room_type_id, room_number="101"):
    r = Room(
        property_id=property_id, room_type_id=room_type_id, room_number=room_number
    )
    db.add(r)
    db.commit()
    return r


def make_guest(db, email="guest@test.com", phone="+1-555-0100"):
    g = Guest(first_name="Alice", last_name="Smith", email=email, phone=phone)
    db.add(g)
    db.commit()
    return g


def make_rate_plan(db, property_id, room_type_id, policy="flexible"):
    rp = RatePlan(
        property_id=property_id,
        room_type_id=room_type_id,
        code="BAR",
        name="Best Available",
        base_rate=Decimal("150"),
        valid_from=date.today() - timedelta(days=30),
        valid_to=date.today() + timedelta(days=365),
        cancellation_policy=policy,
    )
    db.add(rp)
    db.commit()
    return rp


def make_reservation(
    db,
    property_id,
    guest_id,
    room_type_id,
    rate_plan_id=None,
    confirmation="RES001",
    nights=3,
    status=ReservationStatus.CONFIRMED,
    check_in_offset=0,
):
    ci = date.today() + timedelta(days=check_in_offset)
    co = ci + timedelta(days=nights)
    res = Reservation(
        property_id=property_id,
        guest_id=guest_id,
        room_type_id=room_type_id,
        rate_plan_id=rate_plan_id,
        confirmation_number=confirmation,
        check_in_date=ci,
        check_out_date=co,
        number_of_nights=nights,
        num_adults=2,
        num_children=0,
        nightly_rate=Decimal("150"),
        total_amount=Decimal("150") * nights,
        status=status,
        guarantee_type="credit_card",
        credit_card_last_4="1234",
    )
    db.add(res)
    db.commit()
    return res


def make_stay(
    db, property_id, reservation, guest_id, room_id, status=StayStatus.RESERVED
):
    s = Stay(
        property_id=property_id,
        reservation_id=reservation.id,
        guest_id=guest_id,
        room_id=room_id,
        check_in_date=reservation.check_in_date,
        check_out_date=reservation.check_out_date,
        nightly_rate=reservation.nightly_rate,
        status=status,
    )
    db.add(s)
    db.commit()
    return s


# ---------------------------------------------------------------------------
# Original tests (fixed)
# ---------------------------------------------------------------------------


def test_complete_gate_workflow(test_db):
    """Test complete workflow with all configured gates"""
    prop = make_property(test_db, code="GATE001")
    rt = make_room_type(test_db, prop.id)

    # Add 3 rooms so availability check doesn't trigger low-availability warning
    room = make_room(test_db, prop.id, rt.id, "301")
    make_room(test_db, prop.id, rt.id, "302")
    make_room(test_db, prop.id, rt.id, "303")

    guest = make_guest(test_db)
    rate_plan = make_rate_plan(test_db, prop.id, rt.id)
    reservation = make_reservation(
        test_db,
        prop.id,
        guest.id,
        rt.id,
        rate_plan.id,
        confirmation="GATE-INT-001",
    )
    stay = make_stay(test_db, prop.id, reservation, guest.id, room.id)

    context = {
        "reservation": reservation,
        "stay": stay,
        "room": room,
        "room_type": rt,
        "rate_plan": rate_plan,
        "db": test_db,
        "triggered_by": "integration_test",
        "operation": "check_in",
    }

    executor = GateExecutor(test_db)
    gates = [
        DateValidationGate(),
        OccupancyGate(),
        RateValidationGate(),
        PaymentGate(),
        AvailabilityGate(),
        RoomAssignmentGate(),
        CheckInGate(),
    ]

    result = executor.execute(gates=gates, context=context, record_history=True)

    assert len(result.results) == len(gates)
    assert result.failed_count == 0
    assert result.passed_count >= 5

    history_count = test_db.query(GateExecutionHistory).count()
    assert history_count == len(gates)


def test_gate_executor_stop_on_failure(test_db):
    """Test executor stops execution on blocking failure"""
    prop = make_property(test_db, code="STOP01")
    rt = make_room_type(
        test_db,
        prop.id,
        code="STD",
        base_price=Decimal("100"),
        max_occupancy=2,
        max_adults=2,
        max_children=0,
    )
    guest = make_guest(test_db, email="stop@test.com")

    # Create a valid reservation first, then manually set bad dates via SQL
    # to bypass the ORM validator
    res = make_reservation(
        test_db,
        prop.id,
        guest.id,
        rt.id,
        confirmation="STOP001",
        nights=3,
        status=ReservationStatus.PENDING,
    )

    # Override dates directly to create invalid state for DateValidationGate
    from sqlalchemy import text

    past_date = date.today() - timedelta(days=5)
    test_db.execute(
        text(
            "UPDATE reservations SET check_in_date=:ci, check_out_date=:co, number_of_nights=1 WHERE id=:id"
        ),
        {"ci": str(past_date), "co": str(past_date - timedelta(days=1)), "id": res.id},
    )
    test_db.commit()
    test_db.refresh(res)

    executor = GateExecutor(test_db)
    gates = [
        DateValidationGate(),  # should fail
        OccupancyGate(),  # should NOT run
        RateValidationGate(),  # should NOT run
    ]

    result = executor.execute(
        gates=gates,
        context={"reservation": res},
        stop_on_failure=True,
    )

    assert len(result.results) == 1
    assert result.has_blocking_failures is True
    assert result.results[0].status == GateStatus.FAILED


# ---------------------------------------------------------------------------
# DateValidationGate
# ---------------------------------------------------------------------------


def test_date_validation_no_reservation():
    gate = DateValidationGate()
    result = gate.validate({})
    assert result.status == GateStatus.FAILED


def test_date_validation_night_mismatch(test_db):
    prop = make_property(test_db, code="DV001")
    rt = make_room_type(test_db, prop.id, code="DV")
    guest = make_guest(test_db, email="dv@test.com")
    res = make_reservation(
        test_db, prop.id, guest.id, rt.id, confirmation="DV001", nights=3
    )
    # Manually set wrong number_of_nights
    from sqlalchemy import text

    test_db.execute(
        text("UPDATE reservations SET number_of_nights=5 WHERE id=:id"), {"id": res.id}
    )
    test_db.commit()
    test_db.refresh(res)
    result = DateValidationGate().validate({"reservation": res})
    assert result.status == GateStatus.FAILED


def test_date_validation_long_stay_warning(test_db):
    prop = make_property(test_db, code="DV002")
    rt = make_room_type(test_db, prop.id, code="DV2")
    guest = make_guest(test_db, email="dv2@test.com")
    res = make_reservation(
        test_db, prop.id, guest.id, rt.id, confirmation="DV002", nights=35
    )
    result = DateValidationGate().validate({"reservation": res})
    assert result.status == GateStatus.WARNING


def test_date_validation_pass(test_db):
    prop = make_property(test_db, code="DV003")
    rt = make_room_type(test_db, prop.id, code="DV3")
    guest = make_guest(test_db, email="dv3@test.com")
    res = make_reservation(
        test_db, prop.id, guest.id, rt.id, confirmation="DV003", nights=3
    )
    result = DateValidationGate().validate({"reservation": res})
    assert result.status == GateStatus.PASSED


def test_date_validation_past_checkin(test_db):
    prop = make_property(test_db, code="DV004")
    rt = make_room_type(test_db, prop.id, code="DV4")
    guest = make_guest(test_db, email="dv4@test.com")
    res = make_reservation(
        test_db, prop.id, guest.id, rt.id, confirmation="DV004", nights=3
    )
    from sqlalchemy import text

    old = date.today() - timedelta(days=10)
    test_db.execute(
        text(
            "UPDATE reservations SET check_in_date=:ci, check_out_date=:co WHERE id=:id"
        ),
        {"ci": str(old), "co": str(old + timedelta(days=3)), "id": res.id},
    )
    test_db.commit()
    test_db.refresh(res)
    result = DateValidationGate().validate({"reservation": res})
    assert result.status == GateStatus.FAILED


# ---------------------------------------------------------------------------
# OccupancyGate
# ---------------------------------------------------------------------------


def test_occupancy_gate_no_reservation():
    result = OccupancyGate().validate({})
    assert result.status == GateStatus.FAILED


def test_occupancy_gate_exceeds_adults(test_db):
    prop = make_property(test_db, code="OC001")
    rt = make_room_type(
        test_db, prop.id, code="OC", max_occupancy=2, max_adults=1, max_children=1
    )
    guest = make_guest(test_db, email="oc@test.com")
    res = make_reservation(test_db, prop.id, guest.id, rt.id, confirmation="OC001")
    # 2 adults exceeds max_adults=1
    result = OccupancyGate().validate({"reservation": res, "room_type": rt})
    assert result.status == GateStatus.FAILED


def test_occupancy_gate_pass(test_db):
    prop = make_property(test_db, code="OC002")
    rt = make_room_type(test_db, prop.id, code="OC2")
    guest = make_guest(test_db, email="oc2@test.com")
    res = make_reservation(test_db, prop.id, guest.id, rt.id, confirmation="OC002")
    result = OccupancyGate().validate({"reservation": res, "room_type": rt})
    assert result.status == GateStatus.PASSED


# ---------------------------------------------------------------------------
# PaymentGate
# ---------------------------------------------------------------------------


def test_payment_gate_no_reservation():
    result = PaymentGate().validate({})
    assert result.status == GateStatus.FAILED


def test_payment_gate_no_guarantee(test_db):
    prop = make_property(test_db, code="PAY001")
    rt = make_room_type(test_db, prop.id, code="PAY")
    guest = make_guest(test_db, email="pay@test.com")
    res = make_reservation(test_db, prop.id, guest.id, rt.id, confirmation="PAY001")
    res.guarantee_type = None
    res.credit_card_last_4 = None
    result = PaymentGate().validate({"reservation": res})
    assert result.status in (GateStatus.FAILED, GateStatus.WARNING)


def test_payment_gate_pass(test_db):
    prop = make_property(test_db, code="PAY002")
    rt = make_room_type(test_db, prop.id, code="PAY2")
    guest = make_guest(test_db, email="pay2@test.com")
    res = make_reservation(test_db, prop.id, guest.id, rt.id, confirmation="PAY002")
    result = PaymentGate().validate({"reservation": res})
    assert result.status in (GateStatus.PASSED, GateStatus.WARNING)


# ---------------------------------------------------------------------------
# AvailabilityGate
# ---------------------------------------------------------------------------


def test_availability_gate_no_reservation():
    result = AvailabilityGate().validate({})
    assert result.status == GateStatus.FAILED


def test_availability_gate_no_db(test_db):
    prop = make_property(test_db, code="AV001")
    rt = make_room_type(test_db, prop.id, code="AV")
    guest = make_guest(test_db, email="av@test.com")
    res = make_reservation(test_db, prop.id, guest.id, rt.id, confirmation="AV001")
    result = AvailabilityGate().validate({"reservation": res})
    assert result.status == GateStatus.WARNING


def test_availability_gate_no_rooms(test_db):
    prop = make_property(test_db, code="AV002")
    rt = make_room_type(test_db, prop.id, code="AV2")
    guest = make_guest(test_db, email="av2@test.com")
    res = make_reservation(test_db, prop.id, guest.id, rt.id, confirmation="AV002")
    result = AvailabilityGate().validate({"reservation": res, "db": test_db})
    assert result.status == GateStatus.FAILED


def test_availability_gate_low_availability_warning(test_db):
    prop = make_property(test_db, code="AV003")
    rt = make_room_type(test_db, prop.id, code="AV3")
    guest = make_guest(test_db, email="av3@test.com")
    make_room(test_db, prop.id, rt.id, "101")
    make_room(test_db, prop.id, rt.id, "102")
    res = make_reservation(test_db, prop.id, guest.id, rt.id, confirmation="AV003")
    result = AvailabilityGate().validate({"reservation": res, "db": test_db})
    assert result.status == GateStatus.WARNING


def test_availability_gate_pass(test_db):
    prop = make_property(test_db, code="AV004")
    rt = make_room_type(test_db, prop.id, code="AV4")
    guest = make_guest(test_db, email="av4@test.com")
    for n in ["101", "102", "103", "104"]:
        make_room(test_db, prop.id, rt.id, n)
    res = make_reservation(test_db, prop.id, guest.id, rt.id, confirmation="AV004")
    result = AvailabilityGate().validate({"reservation": res, "db": test_db})
    assert result.status == GateStatus.PASSED


def test_availability_gate_room_not_available(test_db):
    prop = make_property(test_db, code="AV005")
    rt = make_room_type(test_db, prop.id, code="AV5")
    guest = make_guest(test_db, email="av5@test.com")
    room = make_room(test_db, prop.id, rt.id, "201")
    room.occupancy_state = OccupancyState.OCCUPIED
    test_db.commit()
    res = make_reservation(test_db, prop.id, guest.id, rt.id, confirmation="AV005")
    result = AvailabilityGate().validate(
        {"reservation": res, "room": room, "db": test_db}
    )
    assert result.status == GateStatus.FAILED


# ---------------------------------------------------------------------------
# RoomAssignmentGate
# ---------------------------------------------------------------------------


def test_room_assignment_no_reservation():
    result = RoomAssignmentGate().validate({})
    assert result.status == GateStatus.FAILED


def test_room_assignment_no_stay(test_db):
    prop = make_property(test_db, code="RA001")
    rt = make_room_type(test_db, prop.id, code="RA")
    guest = make_guest(test_db, email="ra@test.com")
    res = make_reservation(test_db, prop.id, guest.id, rt.id, confirmation="RA001")
    result = RoomAssignmentGate().validate({"reservation": res})
    assert result.status == GateStatus.FAILED


def test_room_assignment_pass(test_db):
    prop = make_property(test_db, code="RA002")
    rt = make_room_type(test_db, prop.id, code="RA2")
    guest = make_guest(test_db, email="ra2@test.com")
    room = make_room(test_db, prop.id, rt.id, "101")
    res = make_reservation(test_db, prop.id, guest.id, rt.id, confirmation="RA002")
    stay = make_stay(test_db, prop.id, res, guest.id, room.id)
    result = RoomAssignmentGate().validate(
        {"reservation": res, "stay": stay, "room": room}
    )
    assert result.status == GateStatus.PASSED


# ---------------------------------------------------------------------------
# CheckInGate
# ---------------------------------------------------------------------------


def test_checkin_gate_no_reservation():
    result = CheckInGate().validate({})
    assert result.status == GateStatus.FAILED


def test_checkin_gate_not_confirmed(test_db):
    prop = make_property(test_db, code="CI001")
    rt = make_room_type(test_db, prop.id, code="CI")
    guest = make_guest(test_db, email="ci@test.com")
    res = make_reservation(
        test_db,
        prop.id,
        guest.id,
        rt.id,
        confirmation="CI001",
        status=ReservationStatus.PENDING,
    )
    result = CheckInGate().validate({"reservation": res})
    assert result.status == GateStatus.FAILED


def test_checkin_gate_future_date(test_db):
    prop = make_property(test_db, code="CI002")
    rt = make_room_type(test_db, prop.id, code="CI2")
    guest = make_guest(test_db, email="ci2@test.com")
    res = make_reservation(
        test_db, prop.id, guest.id, rt.id, confirmation="CI002", check_in_offset=5
    )
    result = CheckInGate().validate({"reservation": res})
    assert result.status == GateStatus.FAILED


def test_checkin_gate_no_stay(test_db):
    prop = make_property(test_db, code="CI003")
    rt = make_room_type(test_db, prop.id, code="CI3")
    guest = make_guest(test_db, email="ci3@test.com")
    res = make_reservation(test_db, prop.id, guest.id, rt.id, confirmation="CI003")
    result = CheckInGate().validate({"reservation": res})
    assert result.status == GateStatus.FAILED


def test_checkin_gate_room_not_available(test_db):
    prop = make_property(test_db, code="CI004")
    rt = make_room_type(test_db, prop.id, code="CI4")
    guest = make_guest(test_db, email="ci4@test.com")
    room = make_room(test_db, prop.id, rt.id, "101")
    room.occupancy_state = OccupancyState.OCCUPIED
    test_db.commit()
    res = make_reservation(test_db, prop.id, guest.id, rt.id, confirmation="CI004")
    stay = make_stay(test_db, prop.id, res, guest.id, room.id)
    result = CheckInGate().validate({"reservation": res, "stay": stay})
    assert result.status == GateStatus.FAILED


def test_checkin_gate_no_contact_warning(test_db):
    prop = make_property(test_db, code="CI005")
    rt = make_room_type(test_db, prop.id, code="CI5")
    guest = make_guest(test_db, email=None, phone=None)
    room = make_room(test_db, prop.id, rt.id, "101")
    res = make_reservation(test_db, prop.id, guest.id, rt.id, confirmation="CI005")
    stay = make_stay(test_db, prop.id, res, guest.id, room.id)
    result = CheckInGate().validate({"reservation": res, "stay": stay})
    assert result.status == GateStatus.WARNING


def test_checkin_gate_pass(test_db):
    prop = make_property(test_db, code="CI006")
    rt = make_room_type(test_db, prop.id, code="CI6")
    guest = make_guest(test_db, email="ci6@test.com")
    room = make_room(test_db, prop.id, rt.id, "101")
    res = make_reservation(test_db, prop.id, guest.id, rt.id, confirmation="CI006")
    stay = make_stay(test_db, prop.id, res, guest.id, room.id)
    result = CheckInGate().validate({"reservation": res, "stay": stay})
    assert result.status == GateStatus.PASSED


# ---------------------------------------------------------------------------
# CheckOutGate
# ---------------------------------------------------------------------------


def test_checkout_gate_no_reservation():
    result = CheckOutGate().validate({})
    assert result.status == GateStatus.FAILED


def test_checkout_gate_not_checked_in(test_db):
    prop = make_property(test_db, code="CO001")
    rt = make_room_type(test_db, prop.id, code="CO")
    guest = make_guest(test_db, email="co@test.com")
    room = make_room(test_db, prop.id, rt.id, "101")
    res = make_reservation(
        test_db,
        prop.id,
        guest.id,
        rt.id,
        confirmation="CO001",
        status=ReservationStatus.CONFIRMED,
    )
    stay = make_stay(
        test_db, prop.id, res, guest.id, room.id, status=StayStatus.CHECKED_IN
    )
    result = CheckOutGate().validate({"reservation": res, "stay": stay})
    assert result.status == GateStatus.FAILED


def test_checkout_gate_stay_not_checked_in(test_db):
    prop = make_property(test_db, code="CO002")
    rt = make_room_type(test_db, prop.id, code="CO2")
    guest = make_guest(test_db, email="co2@test.com")
    room = make_room(test_db, prop.id, rt.id, "101")
    res = make_reservation(
        test_db,
        prop.id,
        guest.id,
        rt.id,
        confirmation="CO002",
        status=ReservationStatus.CHECKED_IN,
    )
    stay = make_stay(
        test_db, prop.id, res, guest.id, room.id, status=StayStatus.RESERVED
    )
    result = CheckOutGate().validate({"reservation": res, "stay": stay})
    assert result.status == GateStatus.FAILED


def test_checkout_gate_early_checkout_warning(test_db):
    prop = make_property(test_db, code="CO003")
    rt = make_room_type(test_db, prop.id, code="CO3")
    guest = make_guest(test_db, email="co3@test.com")
    room = make_room(test_db, prop.id, rt.id, "101")
    res = make_reservation(
        test_db,
        prop.id,
        guest.id,
        rt.id,
        confirmation="CO003",
        status=ReservationStatus.CHECKED_IN,
        nights=5,
    )
    stay = make_stay(
        test_db, prop.id, res, guest.id, room.id, status=StayStatus.CHECKED_IN
    )
    result = CheckOutGate().validate({"reservation": res, "stay": stay})
    assert result.status == GateStatus.WARNING


def test_checkout_gate_pass(test_db):
    prop = make_property(test_db, code="CO004")
    rt = make_room_type(test_db, prop.id, code="CO4")
    guest = make_guest(test_db, email="co4@test.com")
    room = make_room(test_db, prop.id, rt.id, "101")
    res = make_reservation(
        test_db,
        prop.id,
        guest.id,
        rt.id,
        confirmation="CO004",
        status=ReservationStatus.CHECKED_IN,
        nights=3,
        check_in_offset=-3,
    )
    # Set checkout to today
    from sqlalchemy import text

    test_db.execute(
        text("UPDATE reservations SET check_out_date=:co WHERE id=:id"),
        {"co": str(date.today()), "id": res.id},
    )
    test_db.commit()
    test_db.refresh(res)
    stay = make_stay(
        test_db, prop.id, res, guest.id, room.id, status=StayStatus.CHECKED_IN
    )
    from sqlalchemy import text as t2

    test_db.execute(
        t2("UPDATE stays SET check_out_date=:co WHERE id=:id"),
        {"co": str(date.today()), "id": stay.id},
    )
    test_db.commit()
    test_db.refresh(stay)
    result = CheckOutGate().validate({"reservation": res, "stay": stay})
    assert result.status == GateStatus.PASSED


# ---------------------------------------------------------------------------
# ReservationCancellationGate
# ---------------------------------------------------------------------------


def test_cancellation_gate_no_reservation():
    result = ReservationCancellationGate().validate({})
    assert result.status == GateStatus.FAILED


def test_cancellation_gate_already_cancelled(test_db):
    prop = make_property(test_db, code="CX001")
    rt = make_room_type(test_db, prop.id, code="CX")
    guest = make_guest(test_db, email="cx@test.com")
    res = make_reservation(
        test_db,
        prop.id,
        guest.id,
        rt.id,
        confirmation="CX001",
        status=ReservationStatus.CANCELLED,
    )
    result = ReservationCancellationGate().validate({"reservation": res})
    assert result.status == GateStatus.FAILED


def test_cancellation_gate_checked_out(test_db):
    prop = make_property(test_db, code="CX002")
    rt = make_room_type(test_db, prop.id, code="CX2")
    guest = make_guest(test_db, email="cx2@test.com")
    res = make_reservation(
        test_db,
        prop.id,
        guest.id,
        rt.id,
        confirmation="CX002",
        status=ReservationStatus.CHECKED_OUT,
    )
    result = ReservationCancellationGate().validate({"reservation": res})
    assert result.status == GateStatus.FAILED


def test_cancellation_gate_checked_in_no_force(test_db):
    prop = make_property(test_db, code="CX003")
    rt = make_room_type(test_db, prop.id, code="CX3")
    guest = make_guest(test_db, email="cx3@test.com")
    res = make_reservation(
        test_db,
        prop.id,
        guest.id,
        rt.id,
        confirmation="CX003",
        status=ReservationStatus.CHECKED_IN,
    )
    result = ReservationCancellationGate().validate(
        {"reservation": res, "force_cancel": False}
    )
    assert result.status == GateStatus.FAILED


def test_cancellation_gate_checked_in_force(test_db):
    prop = make_property(test_db, code="CX004")
    rt = make_room_type(test_db, prop.id, code="CX4")
    guest = make_guest(test_db, email="cx4@test.com")
    res = make_reservation(
        test_db,
        prop.id,
        guest.id,
        rt.id,
        confirmation="CX004",
        status=ReservationStatus.CHECKED_IN,
    )
    result = ReservationCancellationGate().validate(
        {"reservation": res, "force_cancel": True}
    )
    assert result.status == GateStatus.WARNING


def test_cancellation_gate_fee_warning_flexible(test_db):
    prop = make_property(test_db, code="CX005")
    rt = make_room_type(test_db, prop.id, code="CX5")
    guest = make_guest(test_db, email="cx5@test.com")
    rate_plan = make_rate_plan(test_db, prop.id, rt.id, policy="flexible")
    # check_in today so days_until_checkin=0 => 10% fee
    res = make_reservation(
        test_db,
        prop.id,
        guest.id,
        rt.id,
        rate_plan.id,
        confirmation="CX005",
        check_in_offset=0,
    )
    result = ReservationCancellationGate().validate({"reservation": res})
    assert result.status == GateStatus.WARNING


def test_cancellation_gate_strict_policy(test_db):
    prop = make_property(test_db, code="CX006")
    rt = make_room_type(test_db, prop.id, code="CX6")
    guest = make_guest(test_db, email="cx6@test.com")
    rate_plan = make_rate_plan(test_db, prop.id, rt.id, policy="strict")
    res = make_reservation(
        test_db,
        prop.id,
        guest.id,
        rt.id,
        rate_plan.id,
        confirmation="CX006",
        check_in_offset=5,
    )
    result = ReservationCancellationGate().validate({"reservation": res})
    assert result.status == GateStatus.WARNING  # fee = full amount


def test_cancellation_gate_pass_no_fee(test_db):
    prop = make_property(test_db, code="CX007")
    rt = make_room_type(test_db, prop.id, code="CX7")
    guest = make_guest(test_db, email="cx7@test.com")
    rate_plan = make_rate_plan(test_db, prop.id, rt.id, policy="flexible")
    # checkin far in future => no fee
    res = make_reservation(
        test_db,
        prop.id,
        guest.id,
        rt.id,
        rate_plan.id,
        confirmation="CX007",
        check_in_offset=10,
    )
    result = ReservationCancellationGate().validate({"reservation": res})
    assert result.status == GateStatus.PASSED


def test_cancellation_gate_moderate_policy_no_fee(test_db):
    prop = make_property(test_db, code="CX008")
    rt = make_room_type(test_db, prop.id, code="CX8")
    guest = make_guest(test_db, email="cx8@test.com")
    rate_plan = make_rate_plan(test_db, prop.id, rt.id, policy="moderate")
    res = make_reservation(
        test_db,
        prop.id,
        guest.id,
        rt.id,
        rate_plan.id,
        confirmation="CX008",
        check_in_offset=10,
    )
    result = ReservationCancellationGate().validate({"reservation": res})
    assert result.status == GateStatus.PASSED


def test_cancellation_gate_no_rate_plan_fee(test_db):
    prop = make_property(test_db, code="CX009")
    rt = make_room_type(test_db, prop.id, code="CX9")
    guest = make_guest(test_db, email="cx9@test.com")
    # No rate plan, check_in tomorrow => fee applies (< 2 days)
    res = make_reservation(
        test_db, prop.id, guest.id, rt.id, confirmation="CX009", check_in_offset=1
    )
    result = ReservationCancellationGate().validate({"reservation": res})
    assert result.status == GateStatus.WARNING


# ---------------------------------------------------------------------------
# RateValidationGate
# ---------------------------------------------------------------------------


def test_rate_validation_no_reservation():
    result = RateValidationGate().validate({})
    assert result.status == GateStatus.FAILED


def test_rate_validation_pass(test_db):
    prop = make_property(test_db, code="RV001")
    rt = make_room_type(test_db, prop.id, code="RV")
    guest = make_guest(test_db, email="rv@test.com")
    rate_plan = make_rate_plan(test_db, prop.id, rt.id)
    res = make_reservation(
        test_db, prop.id, guest.id, rt.id, rate_plan.id, confirmation="RV001"
    )
    result = RateValidationGate().validate({"reservation": res, "rate_plan": rate_plan})
    assert result.status in (GateStatus.PASSED, GateStatus.WARNING)


# ---------------------------------------------------------------------------
# GateExecutor extras
# ---------------------------------------------------------------------------


def test_executor_no_db_no_history(test_db):
    prop = make_property(test_db, code="EX001")
    rt = make_room_type(test_db, prop.id, code="EX")
    guest = make_guest(test_db, email="ex@test.com")
    res = make_reservation(test_db, prop.id, guest.id, rt.id, confirmation="EX001")
    executor = GateExecutor(db=None)
    result = executor.execute(
        gates=[DateValidationGate()],
        context={"reservation": res},
        record_history=False,
    )
    assert len(result.results) == 1


def test_executor_all_passed_property(test_db):
    prop = make_property(test_db, code="EX002")
    rt = make_room_type(test_db, prop.id, code="EX2")
    guest = make_guest(test_db, email="ex2@test.com")
    res = make_reservation(test_db, prop.id, guest.id, rt.id, confirmation="EX002")
    executor = GateExecutor(test_db)
    result = executor.execute(
        gates=[DateValidationGate()],
        context={"reservation": res},
        record_history=False,
    )
    assert result.all_passed is True
    assert result.has_failures is False
    assert result.to_dict()["total_gates"] == 1
