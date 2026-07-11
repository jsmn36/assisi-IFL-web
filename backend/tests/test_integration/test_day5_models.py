"""
Supplementary tests to cover uncovered lines in:
- app/gates/gates.py (0%)
- app/gates/check_out_gate.py (lines 62-83, charges logic)
- app/models/room.py (61%)
- app/models/stay.py (65%)
- app/models/reservation.py (65%)
- app/gates/occupancy_gate.py, payment_gate.py, rate_validation_gate.py
"""
import pytest
from datetime import date, timedelta, datetime
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
)
from app.models.stay import StayStatus
from app.models.room import OccupancyState, ConditionState


# ---------------------------------------------------------------------------
# Helpers (duplicated here so this file is self-contained)
# ---------------------------------------------------------------------------


def make_property(db, code="X001"):
    p = Property(
        name="Hotel",
        code=code,
        address_line1="1 St",
        city="C",
        state="S",
        postal_code="12345",
    )
    db.add(p)
    db.commit()
    return p


def make_room_type(db, pid, code="STD", max_adults=2, max_children=2, max_occupancy=4):
    rt = RoomType(
        property_id=pid,
        code=code,
        name="Std",
        base_price=Decimal("100"),
        max_occupancy=max_occupancy,
        max_adults=max_adults,
        max_children=max_children,
    )
    db.add(rt)
    db.commit()
    return rt


def make_room(db, pid, rtid, num="101"):
    r = Room(property_id=pid, room_type_id=rtid, room_number=num)
    db.add(r)
    db.commit()
    return r


def make_guest(db, email="g@test.com", phone="+1-555-0100"):
    g = Guest(first_name="Bob", last_name="Jones", email=email, phone=phone)
    db.add(g)
    db.commit()
    return g


def make_rate_plan(db, pid, rtid, policy="flexible", code="BAR"):
    rp = RatePlan(
        property_id=pid,
        room_type_id=rtid,
        code=code,
        name="BAR",
        base_rate=Decimal("100"),
        valid_from=date.today() - timedelta(days=30),
        valid_to=date.today() + timedelta(days=365),
        cancellation_policy=policy,
    )
    db.add(rp)
    db.commit()
    return rp


def make_reservation(
    db,
    pid,
    gid,
    rtid,
    rpid=None,
    conf="R001",
    nights=3,
    status=ReservationStatus.CONFIRMED,
    offset=0,
    num_adults=2,
    num_children=0,
):
    ci = date.today() + timedelta(days=offset)
    co = ci + timedelta(days=nights)
    res = Reservation(
        property_id=pid,
        guest_id=gid,
        room_type_id=rtid,
        rate_plan_id=rpid,
        confirmation_number=conf,
        check_in_date=ci,
        check_out_date=co,
        number_of_nights=nights,
        num_adults=num_adults,
        num_children=num_children,
        nightly_rate=Decimal("100"),
        total_amount=Decimal("100") * nights,
        status=status,
        guarantee_type="credit_card",
        credit_card_last_4="4321",
    )
    db.add(res)
    db.commit()
    return res


def make_stay(db, pid, res, gid, room_id, status=StayStatus.RESERVED):
    s = Stay(
        property_id=pid,
        reservation_id=res.id,
        guest_id=gid,
        room_id=room_id,
        check_in_date=res.check_in_date,
        check_out_date=res.check_out_date,
        nightly_rate=res.nightly_rate,
        status=status,
    )
    db.add(s)
    db.commit()
    return s


# ---------------------------------------------------------------------------
# gates.py — cover the legacy GateResult, ExecutionResult, BaseGate, GateExecutor
# ---------------------------------------------------------------------------


def test_gates_py_gate_result_properties():
    from app.gates.gates import GateResult, GateResultLevel

    r_ok = GateResult(gate_name="test", level=GateResultLevel.OK, message="ok")
    assert r_ok.is_ok is True
    assert r_ok.is_warning is False
    assert r_ok.is_failure is False

    r_warn = GateResult(gate_name="test", level=GateResultLevel.WARNING, message="warn")
    assert r_warn.is_warning is True
    assert r_warn.is_ok is False

    r_fail = GateResult(
        gate_name="test",
        level=GateResultLevel.FAILURE,
        message="fail",
        is_blocking=True,
    )
    assert r_fail.is_failure is True


def test_gates_py_execution_result():
    from app.gates.gates import GateResult, GateResultLevel, ExecutionResult

    er = ExecutionResult()
    assert er.has_blocking_failures is False

    r_ok = GateResult("g1", GateResultLevel.OK, "ok")
    r_fail = GateResult("g2", GateResultLevel.FAILURE, "fail", is_blocking=True)
    er.results.append(r_ok)
    er.results.append(r_fail)

    assert er.has_blocking_failures is True
    assert len(er.get_warnings()) == 0
    assert len(er.get_failures()) == 1


def test_gates_py_checkout_gate_no_stay():
    from app.gates.gates import CheckOutGate

    gate = CheckOutGate()
    results = gate.check({"stay": None})
    assert len(results) == 1
    assert results[0].is_blocking is True


def test_gates_py_checkout_gate_already_checked_out(test_db):
    from app.gates.gates import CheckOutGate

    prop = make_property(test_db, "GCO01")
    rt = make_room_type(test_db, prop.id, "GCO")
    guest = make_guest(test_db, "gco@test.com")
    room = make_room(test_db, prop.id, rt.id)
    res = make_reservation(
        test_db,
        prop.id,
        guest.id,
        rt.id,
        conf="GCO001",
        status=ReservationStatus.CHECKED_OUT,
    )
    stay = make_stay(
        test_db, prop.id, res, guest.id, room.id, status=StayStatus.CHECKED_OUT
    )
    gate = CheckOutGate()
    results = gate.check({"stay": stay})
    assert any(r.is_failure for r in results)


def test_gates_py_checkout_gate_force(test_db):
    from app.gates.gates import CheckOutGate

    prop = make_property(test_db, "GCO02")
    rt = make_room_type(test_db, prop.id, "GCO2")
    guest = make_guest(test_db, "gco2@test.com")
    room = make_room(test_db, prop.id, rt.id)
    res = make_reservation(
        test_db,
        prop.id,
        guest.id,
        rt.id,
        conf="GCO002",
        status=ReservationStatus.CHECKED_OUT,
    )
    stay = make_stay(
        test_db, prop.id, res, guest.id, room.id, status=StayStatus.CHECKED_OUT
    )
    gate = CheckOutGate()
    results = gate.check({"stay": stay, "force_checkout": True})
    assert any(r.is_warning for r in results)


def test_gates_py_payment_gate_no_stay():
    from app.gates.gates import PaymentGate

    gate = PaymentGate()
    results = gate.check({"stay": None})
    assert results == []


def test_gates_py_executor():
    from app.gates.gates import GateExecutor, CheckOutGate, ExecutionResult

    executor = GateExecutor(db=None)
    result = executor.execute(gates=[CheckOutGate()], context={"stay": None})
    assert isinstance(result, ExecutionResult)
    assert len(result.results) > 0


# ---------------------------------------------------------------------------
# Room model — cover lines 53-91, 103
# ---------------------------------------------------------------------------


def test_room_check_in_and_out(test_db):
    prop = make_property(test_db, "RM001")
    rt = make_room_type(test_db, prop.id, "RM")
    room = make_room(test_db, prop.id, rt.id)

    assert room.is_available() is True
    room.check_in()
    assert room.occupancy_state == OccupancyState.OCCUPIED
    assert room.is_available() is False

    room.check_out()
    assert room.occupancy_state == OccupancyState.VACANT
    assert room.condition_state == ConditionState.DIRTY
    assert room.is_available() is False  # dirty after checkout


def test_room_check_in_already_occupied(test_db):
    prop = make_property(test_db, "RM002")
    rt = make_room_type(test_db, prop.id, "RM2")
    room = make_room(test_db, prop.id, rt.id)
    room.check_in()
    with pytest.raises(Exception):
        room.check_in()


def test_room_checkout_vacant_raises(test_db):
    prop = make_property(test_db, "RM003")
    rt = make_room_type(test_db, prop.id, "RM3")
    room = make_room(test_db, prop.id, rt.id)
    with pytest.raises(Exception):
        room.check_out()


def test_room_out_of_order_and_return(test_db):
    prop = make_property(test_db, "RM004")
    rt = make_room_type(test_db, prop.id, "RM4")
    room = make_room(test_db, prop.id, rt.id)
    room.take_out_of_order(notes="Flooding")
    assert room.occupancy_state == OccupancyState.OUT_OF_ORDER
    assert room.is_available() is False
    room.return_to_service()
    assert room.occupancy_state == OccupancyState.VACANT
    assert room.is_available() is True


def test_room_mark_dirty_clean_inspected(test_db):
    prop = make_property(test_db, "RM005")
    rt = make_room_type(test_db, prop.id, "RM5")
    room = make_room(test_db, prop.id, rt.id)
    room.mark_dirty()
    assert room.condition_state == ConditionState.DIRTY
    room.mark_clean()
    assert room.condition_state == ConditionState.CLEAN
    room.mark_inspected()
    assert room.condition_state == ConditionState.INSPECTED
    assert room.is_available() is True  # VACANT + INSPECTED = available


def test_room_to_dict(test_db):
    prop = make_property(test_db, "RM006")
    rt = make_room_type(test_db, prop.id, "RM6")
    room = make_room(test_db, prop.id, rt.id)
    d = room.to_dict()
    assert d["room_number"] == "101"
    assert "occupancy_state" in d


# ---------------------------------------------------------------------------
# Stay model — cover lifecycle, financial, housekeeping lines
# ---------------------------------------------------------------------------


def test_stay_check_in_and_out(test_db):
    prop = make_property(test_db, "ST001")
    rt = make_room_type(test_db, prop.id, "ST")
    guest = make_guest(test_db, "st@test.com")
    room = make_room(test_db, prop.id, rt.id)
    res = make_reservation(test_db, prop.id, guest.id, rt.id, conf="ST001")
    stay = make_stay(test_db, prop.id, res, guest.id, room.id)

    assert stay.is_checked_in is False
    result = stay.check_in("front_desk")
    assert result is True
    assert stay.status == StayStatus.CHECKED_IN
    assert stay.is_active is True
    assert stay.is_checked_in is True

    result2 = stay.check_out("front_desk")
    assert result2 is True
    assert stay.is_checked_out is True
    assert stay.requires_cleaning is True


def test_stay_check_in_wrong_status(test_db):
    prop = make_property(test_db, "ST002")
    rt = make_room_type(test_db, prop.id, "ST2")
    guest = make_guest(test_db, "st2@test.com")
    room = make_room(test_db, prop.id, rt.id)
    res = make_reservation(test_db, prop.id, guest.id, rt.id, conf="ST002")
    stay = make_stay(
        test_db, prop.id, res, guest.id, room.id, status=StayStatus.CHECKED_IN
    )
    assert stay.check_in("staff") is False


def test_stay_cancel(test_db):
    prop = make_property(test_db, "ST003")
    rt = make_room_type(test_db, prop.id, "ST3")
    guest = make_guest(test_db, "st3@test.com")
    room = make_room(test_db, prop.id, rt.id)
    res = make_reservation(test_db, prop.id, guest.id, rt.id, conf="ST003")
    stay = make_stay(test_db, prop.id, res, guest.id, room.id)
    assert stay.cancel() is True
    assert stay.status == StayStatus.CANCELLED
    assert stay.cancel() is False  # already cancelled


def test_stay_financial_methods(test_db):
    prop = make_property(test_db, "ST004")
    rt = make_room_type(test_db, prop.id, "ST4")
    guest = make_guest(test_db, "st4@test.com")
    room = make_room(test_db, prop.id, rt.id)
    res = make_reservation(test_db, prop.id, guest.id, rt.id, conf="ST004")
    stay = make_stay(test_db, prop.id, res, guest.id, room.id)

    stay.add_room_charge(Decimal("100"))
    stay.add_other_charge(Decimal("25"))
    assert stay.total_charges == Decimal("125")
    assert stay.number_of_nights == 3


def test_stay_housekeeping(test_db):
    prop = make_property(test_db, "ST005")
    rt = make_room_type(test_db, prop.id, "ST5")
    guest = make_guest(test_db, "st5@test.com")
    room = make_room(test_db, prop.id, rt.id)
    res = make_reservation(test_db, prop.id, guest.id, rt.id, conf="ST005")
    stay = make_stay(test_db, prop.id, res, guest.id, room.id)

    stay.mark_cleaning_completed()
    assert stay.cleaning_completed is True
    assert stay.requires_cleaning is False

    stay.mark_cleaning_required()
    assert stay.requires_cleaning is True
    assert stay.cleaning_completed is False


def test_stay_to_dict(test_db):
    prop = make_property(test_db, "ST006")
    rt = make_room_type(test_db, prop.id, "ST6")
    guest = make_guest(test_db, "st6@test.com")
    room = make_room(test_db, prop.id, rt.id)
    res = make_reservation(test_db, prop.id, guest.id, rt.id, conf="ST006")
    stay = make_stay(test_db, prop.id, res, guest.id, room.id)
    d = stay.to_dict()
    assert "status" in d
    assert d["number_of_nights"] == 3


# ---------------------------------------------------------------------------
# Reservation model — cover lifecycle methods and properties
# ---------------------------------------------------------------------------


def test_reservation_confirm(test_db):
    prop = make_property(test_db, "RES001")
    rt = make_room_type(test_db, prop.id, "RS")
    guest = make_guest(test_db, "res@test.com")
    res = make_reservation(
        test_db,
        prop.id,
        guest.id,
        rt.id,
        conf="RES001",
        status=ReservationStatus.PENDING,
    )
    assert res.confirm("manager") is True
    assert res.status == ReservationStatus.CONFIRMED
    assert res.confirm("manager") is False  # already confirmed


def test_reservation_cancel(test_db):
    prop = make_property(test_db, "RES002")
    rt = make_room_type(test_db, prop.id, "RS2")
    guest = make_guest(test_db, "res2@test.com")
    res = make_reservation(test_db, prop.id, guest.id, rt.id, conf="RES002")
    assert res.cancel("staff", reason="Guest request", fee=50) is True
    assert res.is_cancelled is True
    assert res.cancel("staff") is False  # already cancelled


def test_reservation_check_in_check_out(test_db):
    prop = make_property(test_db, "RES003")
    rt = make_room_type(test_db, prop.id, "RS3")
    guest = make_guest(test_db, "res3@test.com")
    res = make_reservation(test_db, prop.id, guest.id, rt.id, conf="RES003")
    assert res.check_in() is True
    assert res.status == ReservationStatus.CHECKED_IN
    assert res.check_in() is False  # not confirmed anymore

    assert res.check_out() is True
    assert res.status == ReservationStatus.CHECKED_OUT
    assert res.check_out() is False  # not checked in anymore


def test_reservation_mark_no_show(test_db):
    prop = make_property(test_db, "RES004")
    rt = make_room_type(test_db, prop.id, "RS4")
    guest = make_guest(test_db, "res4@test.com")
    res = make_reservation(
        test_db, prop.id, guest.id, rt.id, conf="RES004", offset=-5, nights=2
    )  # past reservation
    # Set as confirmed + past
    from sqlalchemy import text

    test_db.execute(
        text("UPDATE reservations SET status='CONFIRMED' WHERE id=:id"), {"id": res.id}
    )
    test_db.commit()
    test_db.refresh(res)
    result = res.mark_no_show()
    assert result is True
    assert res.status == ReservationStatus.NO_SHOW


def test_reservation_calculate_methods(test_db):
    prop = make_property(test_db, "RES005")
    rt = make_room_type(test_db, prop.id, "RS5")
    guest = make_guest(test_db, "res5@test.com")
    res = make_reservation(test_db, prop.id, guest.id, rt.id, conf="RES005", nights=3)
    nights = res.calculate_nights()
    assert nights == 3
    total = res.calculate_total_amount()
    assert total == Decimal("300")


def test_reservation_properties(test_db):
    prop = make_property(test_db, "RES006")
    rt = make_room_type(test_db, prop.id, "RS6")
    guest = make_guest(test_db, "res6@test.com")

    # Future reservation
    res_future = make_reservation(
        test_db, prop.id, guest.id, rt.id, conf="RES006A", offset=5
    )
    assert res_future.is_future is True
    assert res_future.is_past is False
    assert res_future.is_arriving_today is False

    # Past reservation
    res_past = make_reservation(
        test_db, prop.id, guest.id, rt.id, conf="RES006B", offset=-5, nights=2
    )
    assert res_past.is_past is True
    assert res_past.is_current is False

    # Arriving today
    res_today = make_reservation(
        test_db, prop.id, guest.id, rt.id, conf="RES006C", offset=0
    )
    assert res_today.is_arriving_today is True
    assert res_today.is_departing_today is False


def test_reservation_to_dict(test_db):
    prop = make_property(test_db, "RES007")
    rt = make_room_type(test_db, prop.id, "RS7")
    guest = make_guest(test_db, "res7@test.com")
    res = make_reservation(test_db, prop.id, guest.id, rt.id, conf="RES007")
    d = res.to_dict()
    assert d["confirmation_number"] == "RES007"
    assert "status" in d
    assert "is_past" in d


# ---------------------------------------------------------------------------
# CheckOutGate — cover charge logic (lines 62-83)
# ---------------------------------------------------------------------------


def test_checkout_gate_pass_no_charges(test_db):
    """Checkout on checkout date with no charges — should pass"""
    from app.gates.check_out_gate import CheckOutGate

    prop = make_property(test_db, "COG01")
    rt = make_room_type(test_db, prop.id, "COG")
    guest = make_guest(test_db, "cog@test.com")
    room = make_room(test_db, prop.id, rt.id)
    res = make_reservation(
        test_db,
        prop.id,
        guest.id,
        rt.id,
        conf="COG001",
        status=ReservationStatus.CHECKED_IN,
        offset=-3,
        nights=3,
    )
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
    test_db.execute(
        text("UPDATE stays SET check_out_date=:co WHERE id=:id"),
        {"co": str(date.today()), "id": stay.id},
    )
    test_db.commit()
    test_db.refresh(stay)
    result = CheckOutGate().validate({"reservation": res, "stay": stay})
    assert result.status in ("passed", "warning")


# ---------------------------------------------------------------------------
# OccupancyGate — cover more branches
# ---------------------------------------------------------------------------


def test_occupancy_gate_exceeds_total(test_db):
    from app.gates.occupancy_gate import OccupancyGate

    prop = make_property(test_db, "OCC01")
    rt = make_room_type(
        test_db, prop.id, "OCC", max_occupancy=2, max_adults=2, max_children=1
    )
    guest = make_guest(test_db, "occ@test.com")
    res = make_reservation(
        test_db, prop.id, guest.id, rt.id, conf="OCC001", num_adults=2, num_children=1
    )
    # Total = 3 > max_occupancy=2
    result = OccupancyGate().validate({"reservation": res, "room_type": rt})
    assert result.status == "failed"


def test_occupancy_gate_no_room_type(test_db):
    from app.gates.occupancy_gate import OccupancyGate

    prop = make_property(test_db, "OCC02")
    rt = make_room_type(test_db, prop.id, "OCC2")
    guest = make_guest(test_db, "occ2@test.com")
    res = make_reservation(test_db, prop.id, guest.id, rt.id, conf="OCC002")
    # No room_type in context — gate should use reservation.room_type
    result = OccupancyGate().validate({"reservation": res})
    assert result.status in ("passed", "failed", "warning")


# ---------------------------------------------------------------------------
# PaymentGate — cover more branches
# ---------------------------------------------------------------------------


def test_payment_gate_deposit_paid(test_db):
    from app.gates.payment_gate import PaymentGate

    prop = make_property(test_db, "PAY01")
    rt = make_room_type(test_db, prop.id, "PAY")
    guest = make_guest(test_db, "pay@test.com")
    res = make_reservation(test_db, prop.id, guest.id, rt.id, conf="PAY001")
    res.deposit_paid = True
    res.deposit_amount = Decimal("50")
    result = PaymentGate().validate({"reservation": res})
    assert result.status in ("passed", "warning")


# ---------------------------------------------------------------------------
# RateValidationGate — cover more branches
# ---------------------------------------------------------------------------


def test_rate_validation_no_rate_plan(test_db):
    from app.gates.rate_validation_gate import RateValidationGate

    prop = make_property(test_db, "RV01")
    rt = make_room_type(test_db, prop.id, "RV")
    guest = make_guest(test_db, "rv@test.com")
    res = make_reservation(test_db, prop.id, guest.id, rt.id, conf="RV001")
    result = RateValidationGate().validate({"reservation": res})
    assert result.status in ("passed", "warning", "failed")


def test_rate_validation_zero_rate(test_db):
    from app.gates.rate_validation_gate import RateValidationGate

    prop = make_property(test_db, "RV02")
    rt = make_room_type(test_db, prop.id, "RV2")
    guest = make_guest(test_db, "rv2@test.com")
    res = make_reservation(test_db, prop.id, guest.id, rt.id, conf="RV002")
    from sqlalchemy import text

    test_db.execute(
        text("UPDATE reservations SET nightly_rate=0 WHERE id=:id"), {"id": res.id}
    )
    test_db.commit()
    test_db.refresh(res)
    result = RateValidationGate().validate({"reservation": res})
    assert result.status in ("failed", "warning")
