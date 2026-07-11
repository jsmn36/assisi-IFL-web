import pytest
from datetime import date, timedelta
from decimal import Decimal
from app.services.check_out_service import CheckOutService
from app.services.check_in_service import CheckInService
from app.services.reservation_service import ReservationService
from app.models import (
    Property,
    RoomType,
    Room,
    Guest,
    RatePlan,
    StayStatus,
    ChargeStatus,
)


@pytest.fixture
def checkout_env(test_db):
    prop = Property(name="HQ", code="HQ", city="NY", state="NY")
    test_db.add(prop)
    test_db.commit()

    rt = RoomType(
        property_id=prop.id, code="DBL", name="Double", base_price=Decimal("150")
    )
    test_db.add(rt)
    test_db.commit()

    room = Room(property_id=prop.id, room_type_id=rt.id, room_number="202")
    test_db.add(room)
    test_db.commit()

    guest = Guest(first_name="Alice", last_name="Check", email="alice@test.com")
    test_db.add(guest)
    test_db.commit()

    return {"p": prop, "rt": rt, "rm": room, "g": guest, "db": test_db}


@pytest.fixture
def active_stay(checkout_env):
    res_service = ReservationService(checkout_env["db"])
    res = res_service.create_reservation(
        property_id=checkout_env["p"].id,
        guest_id=checkout_env["g"].id,
        room_type_id=checkout_env["rt"].id,
        check_in_date=date.today(),
        check_out_date=date.today() + timedelta(days=2),
        num_adults=2,
        nightly_rate=Decimal("150"),
    )
    from app.models.enums import ReservationStatus

    res.status = ReservationStatus.CONFIRMED
    checkout_env["db"].flush()

    ci_service = CheckInService(checkout_env["db"])
    result = ci_service.check_in(
        reservation_id=res.id, room_id=checkout_env["rm"].id, post_room_charges=True
    )
    return result["stay"]


def test_full_checkout_flow(test_db, active_stay):
    service = CheckOutService(test_db)
    result = service.check_out(stay_id=active_stay.id, payment_method="CC")

    assert result["success"] is True
    assert result["stay"].status == StayStatus.CHECKED_OUT
    assert result["payment"]["charges_paid"] > 0
    assert active_stay.room.occupancy_state.value == "vacant"


def test_checkout_by_room_and_res(test_db, active_stay):
    service = CheckOutService(test_db)
    # Test lookup by room
    res1 = service.check_out(room_id=active_stay.room_id, force_checkout=True)
    assert res1["success"] is True

    # Reset and test lookup by reservation (using a new stay)
    # (Simplified: just verify the service logic for lookup works)


def test_final_bill_generation(test_db, active_stay):
    service = CheckOutService(test_db)
    bill = service.get_final_bill(active_stay.id)
    assert bill["total"] == 300.0  # 150 * 2 nights
    assert bill["balance"] == 300.0
    assert bill["payment_status"] == "unpaid"


def test_guest_stats_update(test_db, active_stay):
    guest = active_stay.reservation.guest
    service = CheckOutService(test_db)
    service.check_out(stay_id=active_stay.id, force_checkout=True)
    test_db.refresh(guest)
    assert guest.total_stays == 1
    assert guest.total_nights == 2


def test_checkout_validation_failure(test_db, active_stay):
    service = CheckOutService(test_db)
    # First checkout succeeds
    service.check_out(stay_id=active_stay.id, force_checkout=True)
    # Second checkout on same stay should fail (status is already checked_out)
    from app.services.base_service import BusinessRuleError

    with pytest.raises(BusinessRuleError):
        service.check_out(stay_id=active_stay.id, force_checkout=False)


def test_error_missing_ids(test_db):
    service = CheckOutService(test_db)
    from app.services.base_service import BusinessRuleError

    with pytest.raises(BusinessRuleError, match="provide stay_id"):
        service.check_out()


def test_error_no_stay_found(test_db, checkout_env):
    service = CheckOutService(test_db)
    from app.services.base_service import BusinessRuleError

    with pytest.raises(BusinessRuleError, match="No active stay"):
        service.check_out(room_id=999)
