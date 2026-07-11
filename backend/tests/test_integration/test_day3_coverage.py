"""
Day 3 Additional Coverage Tests
Targets uncovered lines in room, reservation, rate_plan, business_day, stay, guest models
"""
import pytest
from app.models import *
from datetime import date, datetime, timedelta
from decimal import Decimal


# ── Shared fixture helpers ────────────────────────────────────────────────────


def make_property(test_db):
    p = Property(
        name="Test Hotel",
        code="TEST",
        address_line1="1 Main St",
        city="City",
        state="ST",
        postal_code="00000",
    )
    test_db.add(p)
    test_db.commit()
    return p


def make_room_type(test_db, property_id):
    rt = RoomType(
        property_id=property_id, code="STD", name="Standard", base_price=Decimal("100")
    )
    test_db.add(rt)
    test_db.commit()
    return rt


def make_room(test_db, property_id, room_type_id, number="101"):
    r = Room(property_id=property_id, room_type_id=room_type_id, room_number=number)
    test_db.add(r)
    test_db.commit()
    return r


def make_guest(test_db, email="guest@test.com"):
    g = Guest(first_name="Test", last_name="Guest", email=email)
    test_db.add(g)
    test_db.commit()
    return g


def make_reservation(
    test_db, property_id, guest_id, room_type_id, confirmation="RES001", status=None
):
    r = Reservation(
        property_id=property_id,
        guest_id=guest_id,
        room_type_id=room_type_id,
        confirmation_number=confirmation,
        check_in_date=date.today(),
        check_out_date=date.today() + timedelta(days=2),
        number_of_nights=2,
        nightly_rate=Decimal("100"),
        total_amount=Decimal("200"),
    )
    if status:
        r.status = status
    test_db.add(r)
    test_db.commit()
    return r


# ── Room tests ────────────────────────────────────────────────────────────────


def test_room_out_of_order(test_db):
    print("\n🚫 TESTING Room: out-of-order / return-to-service")
    p = make_property(test_db)
    rt = make_room_type(test_db, p.id)
    room = make_room(test_db, p.id, rt.id)

    room.take_out_of_order(notes="Plumbing issue")
    test_db.commit()
    assert room.occupancy_state == OccupancyState.OUT_OF_ORDER
    assert room.notes == "Plumbing issue"
    assert room.is_available() is False

    room.return_to_service()
    test_db.commit()
    assert room.occupancy_state == OccupancyState.VACANT
    assert room.condition_state == ConditionState.CLEAN
    assert room.is_available() is True
    print("   ✅ out-of-order and return-to-service work")


def test_room_mark_dirty_inspected(test_db):
    print("\n🧹 TESTING Room: mark_dirty / mark_inspected")
    p = make_property(test_db)
    rt = make_room_type(test_db, p.id)
    room = make_room(test_db, p.id, rt.id, "102")

    room.mark_dirty()
    test_db.commit()
    assert room.condition_state == ConditionState.DIRTY
    assert room.is_available() is False

    room.mark_inspected()
    test_db.commit()
    assert room.condition_state == ConditionState.INSPECTED
    assert room.is_available() is True
    print("   ✅ mark_dirty and mark_inspected work")


def test_room_check_in_already_occupied_raises(test_db):
    print("\n⚠️  TESTING Room: check_in on occupied room raises")
    p = make_property(test_db)
    rt = make_room_type(test_db, p.id)
    room = make_room(test_db, p.id, rt.id, "103")

    room.check_in()
    test_db.commit()
    with pytest.raises(Exception, match="already occupied"):
        room.check_in()
    print("   ✅ double check-in raises correctly")


def test_room_check_out_vacant_raises(test_db):
    print("\n⚠️  TESTING Room: check_out on vacant room raises")
    p = make_property(test_db)
    rt = make_room_type(test_db, p.id)
    room = make_room(test_db, p.id, rt.id, "104")

    with pytest.raises(Exception, match="Cannot check out"):
        room.check_out()
    print("   ✅ check-out on vacant raises correctly")


def test_room_to_dict(test_db):
    print("\n📋 TESTING Room: to_dict")
    p = make_property(test_db)
    rt = make_room_type(test_db, p.id)
    room = make_room(test_db, p.id, rt.id, "105")

    d = room.to_dict()
    assert d["room_number"] == "105"
    assert "occupancy_state" in d
    assert "condition_state" in d
    print("   ✅ to_dict works")


# ── Reservation tests ─────────────────────────────────────────────────────────


def test_reservation_cancel(test_db):
    print("\n❌ TESTING Reservation: cancel")
    p = make_property(test_db)
    rt = make_room_type(test_db, p.id)
    g = make_guest(test_db, "cancel@test.com")
    res = make_reservation(
        test_db, p.id, g.id, rt.id, "CANCEL001", status=ReservationStatus.CONFIRMED
    )

    result = res.cancel(cancelled_by="manager", reason="Guest request", fee=50)
    test_db.commit()

    assert result is True
    assert res.status == ReservationStatus.CANCELLED
    assert res.is_cancelled is True
    assert res.cancellation_reason == "Guest request"
    assert res.cancellation_fee == 50

    # Cancelling again should return False
    assert res.cancel(cancelled_by="manager") is False
    print("   ✅ cancel works")


def test_reservation_no_show(test_db):
    print("\n🚫 TESTING Reservation: mark_no_show")
    p = make_property(test_db)
    rt = make_room_type(test_db, p.id)
    g = make_guest(test_db, "noshow@test.com")

    res = Reservation(
        property_id=p.id,
        guest_id=g.id,
        room_type_id=rt.id,
        confirmation_number="NOSHOW001",
        check_in_date=date.today() - timedelta(days=3),
        check_out_date=date.today() - timedelta(days=1),
        number_of_nights=2,
        nightly_rate=Decimal("100"),
        total_amount=Decimal("200"),
        status=ReservationStatus.CONFIRMED,
    )
    test_db.add(res)
    test_db.commit()

    result = res.mark_no_show()
    test_db.commit()
    assert result is True
    assert res.status == ReservationStatus.NO_SHOW
    print("   ✅ mark_no_show works")


def test_reservation_properties(test_db):
    print("\n📋 TESTING Reservation: is_past / is_future / is_current properties")
    p = make_property(test_db)
    rt = make_room_type(test_db, p.id)
    g = make_guest(test_db, "props@test.com")

    # Future reservation
    future = Reservation(
        property_id=p.id,
        guest_id=g.id,
        room_type_id=rt.id,
        confirmation_number="FUTURE001",
        check_in_date=date.today() + timedelta(days=5),
        check_out_date=date.today() + timedelta(days=7),
        number_of_nights=2,
        nightly_rate=Decimal("100"),
        total_amount=Decimal("200"),
    )
    test_db.add(future)

    # Past reservation
    past = Reservation(
        property_id=p.id,
        guest_id=g.id,
        room_type_id=rt.id,
        confirmation_number="PAST001",
        check_in_date=date.today() - timedelta(days=5),
        check_out_date=date.today() - timedelta(days=3),
        number_of_nights=2,
        nightly_rate=Decimal("100"),
        total_amount=Decimal("200"),
    )
    test_db.add(past)
    test_db.commit()

    assert future.is_future is True
    assert future.is_past is False
    assert past.is_past is True
    assert past.is_future is False
    assert future.is_arriving_today is False
    assert past.is_departing_today is False
    print("   ✅ reservation properties work")


def test_reservation_to_dict(test_db):
    print("\n📋 TESTING Reservation: to_dict")
    p = make_property(test_db)
    rt = make_room_type(test_db, p.id)
    g = make_guest(test_db, "dict@test.com")
    res = make_reservation(test_db, p.id, g.id, rt.id, "DICT001")

    d = res.to_dict()
    assert d["confirmation_number"] == "DICT001"
    assert "status" in d
    assert "total_amount" in d
    print("   ✅ to_dict works")


# ── RatePlan tests ────────────────────────────────────────────────────────────


def test_rate_plan_is_valid_for_date(test_db):
    print("\n📋 TESTING RatePlan: is_valid_for_date / get_rate_for_date")
    p = make_property(test_db)
    rt = make_room_type(test_db, p.id)

    plan = RatePlan(
        property_id=p.id,
        room_type_id=rt.id,
        code="VALID",
        name="Valid Plan",
        base_rate=Decimal("100"),
        weekend_rate=Decimal("150"),
        valid_from=date.today() - timedelta(days=10),
        valid_to=date.today() + timedelta(days=10),
    )
    test_db.add(plan)
    test_db.commit()

    assert plan.is_valid_for_date(date.today()) is True
    assert plan.is_valid_for_date(date.today() - timedelta(days=20)) is False
    assert plan.is_currently_valid is True

    # Weekend rate
    next_saturday = date.today() + timedelta((5 - date.today().weekday()) % 7)
    rate = plan.get_rate_for_date(next_saturday)
    assert rate == Decimal("150")

    # Weekday rate
    next_monday = date.today() + timedelta((7 - date.today().weekday()) % 7)
    rate = plan.get_rate_for_date(next_monday)
    assert rate == Decimal("100")
    print("   ✅ is_valid_for_date and get_rate_for_date work")


def test_rate_plan_inactive(test_db):
    print("\n📋 TESTING RatePlan: inactive plan is not valid")
    p = make_property(test_db)
    rt = make_room_type(test_db, p.id)

    plan = RatePlan(
        property_id=p.id,
        room_type_id=rt.id,
        code="INACTIVE",
        name="Inactive Plan",
        base_rate=Decimal("100"),
        valid_from=date.today() - timedelta(days=10),
        is_active=False,
    )
    test_db.add(plan)
    test_db.commit()

    assert plan.is_currently_valid is False
    assert plan.is_valid_for_date(date.today()) is False
    print("   ✅ inactive plan correctly invalid")


def test_rate_plan_expired(test_db):
    print("\n📋 TESTING RatePlan: expired plan is not valid")
    p = make_property(test_db)
    rt = make_room_type(test_db, p.id)

    plan = RatePlan(
        property_id=p.id,
        room_type_id=rt.id,
        code="EXPIRED",
        name="Expired Plan",
        base_rate=Decimal("100"),
        valid_from=date.today() - timedelta(days=30),
        valid_to=date.today() - timedelta(days=5),
    )
    test_db.add(plan)
    test_db.commit()

    assert plan.is_currently_valid is False
    print("   ✅ expired plan correctly invalid")


def test_rate_plan_to_dict(test_db):
    print("\n📋 TESTING RatePlan: to_dict")
    p = make_property(test_db)
    rt = make_room_type(test_db, p.id)

    plan = RatePlan(
        property_id=p.id,
        room_type_id=rt.id,
        code="DICT",
        name="Dict Plan",
        base_rate=Decimal("100"),
        valid_from=date.today(),
    )
    test_db.add(plan)
    test_db.commit()

    d = plan.to_dict()
    assert d["code"] == "DICT"
    assert "base_rate" in d
    assert "is_currently_valid" in d
    print("   ✅ to_dict works")


# ── BusinessDay tests ─────────────────────────────────────────────────────────


def test_business_day_full_lifecycle(test_db):
    print("\n📅 TESTING BusinessDay: full lifecycle")
    p = make_property(test_db)

    bd = BusinessDay(
        property_id=p.id,
        business_date=date.today(),
    )
    test_db.add(bd)
    test_db.commit()

    # Open
    bd.open_day(opened_by="manager")
    test_db.commit()
    assert bd.status == DayStatus.OPEN
    assert bd.day_opened_by == "manager"

    # Start audit
    bd.start_night_audit(run_by="auditor")
    test_db.commit()
    assert bd.status == DayStatus.IN_AUDIT
    assert bd.night_audit_status == "pending"

    # Set all audit checks
    bd.audit_check_1_result = True
    bd.audit_check_2_result = True
    bd.audit_check_3_result = True
    bd.audit_check_4_result = True
    bd.audit_check_5_result = True
    bd.audit_check_6_result = True
    bd.audit_check_7_result = True
    bd.audit_check_8_result = True
    test_db.commit()

    assert bd.all_audit_checks_passed() is True

    # Complete audit - success
    bd.complete_night_audit(all_checks_passed=True)
    test_db.commit()
    assert bd.status == DayStatus.CLOSED
    assert bd.night_audit_status == "success"

    # close_day is a no-op when already CLOSED (guard in the model)
    bd.close_day(closed_by="manager")
    test_db.commit()
    assert bd.status == DayStatus.CLOSED

    print("   ✅ BusinessDay full lifecycle works")


def test_business_day_failed_audit(test_db):
    print("\n📅 TESTING BusinessDay: failed audit")
    p = make_property(test_db)

    bd = BusinessDay(
        property_id=p.id,
        business_date=date.today() - timedelta(days=1),
    )
    test_db.add(bd)
    test_db.commit()

    bd.start_night_audit(run_by="auditor")
    bd.audit_check_1_result = False  # One check failed
    bd.complete_night_audit(all_checks_passed=False)
    test_db.commit()

    assert bd.status == DayStatus.AUDIT_FAILED
    assert bd.night_audit_status == "failed"
    assert bd.all_audit_checks_passed() is False
    print("   ✅ failed audit works")


def test_business_day_calculate_metrics(test_db):
    print("\n📅 TESTING BusinessDay: calculate_metrics")
    p = make_property(test_db)

    bd = BusinessDay(
        property_id=p.id,
        business_date=date.today() - timedelta(days=2),
        total_occupancy=8,
        room_revenue=Decimal("800"),
        total_revenue=Decimal("1000"),
    )
    test_db.add(bd)
    test_db.commit()

    bd.calculate_metrics(total_rooms=10)
    test_db.commit()

    assert bd.adr == Decimal("100")  # 800 / 8
    assert bd.occupancy_percent == Decimal("80")  # 8/10 * 100
    assert bd.rev_par == Decimal("80")  # 800 / 10
    print("   ✅ calculate_metrics works")


def test_business_day_to_dict(test_db):
    print("\n📅 TESTING BusinessDay: to_dict")
    p = make_property(test_db)

    bd = BusinessDay(
        property_id=p.id,
        business_date=date.today() - timedelta(days=3),
    )
    test_db.add(bd)
    test_db.commit()

    d = bd.to_dict()
    assert d["property_id"] == p.id
    assert "status" in d
    assert "audit_checks_passed" in d
    print("   ✅ to_dict works")


# ── Stay additional tests ─────────────────────────────────────────────────────


def test_stay_cancel(test_db):
    print("\n🛏️  TESTING Stay: cancel")
    p = make_property(test_db)
    rt = make_room_type(test_db, p.id)
    room = make_room(test_db, p.id, rt.id, "201")
    g = make_guest(test_db, "staycancel@test.com")
    res = make_reservation(
        test_db, p.id, g.id, rt.id, "STAYCANCEL001", status=ReservationStatus.CONFIRMED
    )

    stay = Stay(
        property_id=p.id,
        reservation_id=res.id,
        guest_id=g.id,
        room_id=room.id,
        check_in_date=date.today() + timedelta(days=1),
        check_out_date=date.today() + timedelta(days=3),
        nightly_rate=Decimal("100"),
    )
    test_db.add(stay)
    test_db.commit()

    assert stay.status == StayStatus.RESERVED
    result = stay.cancel()
    test_db.commit()
    assert result is True
    assert stay.status == StayStatus.CANCELLED
    print("   ✅ stay cancel works")


def test_stay_properties(test_db):
    print("\n🛏️  TESTING Stay: number_of_nights / is_active / to_dict")
    p = make_property(test_db)
    rt = make_room_type(test_db, p.id)
    room = make_room(test_db, p.id, rt.id, "202")
    g = make_guest(test_db, "stayprops@test.com")
    res = make_reservation(
        test_db, p.id, g.id, rt.id, "STAYPROPS001", status=ReservationStatus.CONFIRMED
    )

    stay = Stay(
        property_id=p.id,
        reservation_id=res.id,
        guest_id=g.id,
        room_id=room.id,
        check_in_date=date.today(),
        check_out_date=date.today() + timedelta(days=3),
        nightly_rate=Decimal("100"),
    )
    test_db.add(stay)
    test_db.commit()

    assert stay.number_of_nights == 3
    assert stay.is_active is False
    assert stay.is_checked_in is False
    assert stay.is_checked_out is False

    stay.check_in(checked_in_by="desk")
    assert stay.is_active is True
    assert stay.is_checked_in is True

    d = stay.to_dict()
    assert "status" in d
    assert d["number_of_nights"] == 3
    print("   ✅ stay properties and to_dict work")


def test_stay_housekeeping_flags(test_db):
    print("\n🧹 TESTING Stay: housekeeping flags")
    p = make_property(test_db)
    rt = make_room_type(test_db, p.id)
    room = make_room(test_db, p.id, rt.id, "203")
    g = make_guest(test_db, "stayhk@test.com")
    res = make_reservation(
        test_db, p.id, g.id, rt.id, "STAYHK001", status=ReservationStatus.CONFIRMED
    )

    stay = Stay(
        property_id=p.id,
        reservation_id=res.id,
        guest_id=g.id,
        room_id=room.id,
        check_in_date=date.today(),
        check_out_date=date.today() + timedelta(days=2),
        nightly_rate=Decimal("100"),
    )
    test_db.add(stay)
    test_db.commit()

    stay.mark_cleaning_completed()
    test_db.commit()
    assert stay.cleaning_completed is True
    assert stay.requires_cleaning is False

    stay.mark_cleaning_required()
    test_db.commit()
    assert stay.requires_cleaning is True
    assert stay.cleaning_completed is False
    print("   ✅ housekeeping flags work")


# ── Guest additional tests ────────────────────────────────────────────────────


def test_guest_blacklist(test_db):
    print("\n🚫 TESTING Guest: blacklist / remove_from_blacklist")
    g = make_guest(test_db, "blacklist@test.com")

    g.blacklist(reason="Damage to property")
    test_db.commit()
    assert g.is_blacklisted is True
    assert g.blacklist_reason == "Damage to property"

    g.remove_from_blacklist()
    test_db.commit()
    assert g.is_blacklisted is False
    assert g.blacklist_reason is None
    print("   ✅ blacklist works")


def test_guest_age_and_to_dict(test_db):
    print("\n👤 TESTING Guest: age property and to_dict")
    from datetime import date as d

    g = Guest(
        first_name="John",
        last_name="Doe",
        email="age@test.com",
        date_of_birth=d(1990, 1, 1),
        middle_name="M",
    )
    test_db.add(g)
    test_db.commit()

    assert g.age is not None
    assert g.age >= 35
    assert g.full_name == "John M Doe"

    dic = g.to_dict()
    assert dic["full_name"] == "John M Doe"
    assert "age" in dic
    print("   ✅ age and to_dict work")
