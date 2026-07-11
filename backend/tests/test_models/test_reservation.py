import pytest
from app.models import Property, RoomType, Guest, Reservation
from app.models import ReservationStatus, ReservationSource
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.exc import IntegrityError


@pytest.fixture
def setup_reservation_data(test_db):
    prop = Property(
        name="Test Hotel",
        code="TEST001",
        address_line1="123 Test St",
        city="Test City",
        state="TC",
        postal_code="12345",
    )
    test_db.add(prop)
    test_db.commit()

    room_type = RoomType(
        code="STD", name="Standard Room", base_price=99.99, property_id=prop.id
    )
    test_db.add(room_type)
    test_db.commit()

    guest = Guest(first_name="John", last_name="Doe", email="john@example.com")
    test_db.add(guest)
    test_db.commit()

    return prop, room_type, guest


def make_res(prop, room_type, guest, conf, **kwargs):
    defaults = dict(
        property_id=prop.id,
        guest_id=guest.id,
        room_type_id=room_type.id,
        confirmation_number=conf,
        check_in_date=date.today() + timedelta(days=7),
        check_out_date=date.today() + timedelta(days=10),
        number_of_nights=3,
        nightly_rate=Decimal("100"),
        total_amount=Decimal("300"),
    )
    defaults.update(kwargs)
    return Reservation(**defaults)


def test_create_reservation(test_db, setup_reservation_data):
    prop, room_type, guest = setup_reservation_data
    res = make_res(prop, room_type, guest, "CONF001", num_adults=2)
    test_db.add(res)
    test_db.commit()
    test_db.refresh(res)
    assert res.id is not None
    assert res.status == ReservationStatus.PENDING
    assert res.number_of_nights == 3


def test_confirmation_number_unique(test_db, setup_reservation_data):
    prop, rt, guest = setup_reservation_data
    test_db.add(make_res(prop, rt, guest, "CONF002"))
    test_db.commit()
    test_db.add(
        make_res(
            prop,
            rt,
            guest,
            "CONF002",
            check_in_date=date.today() + timedelta(days=20),
            check_out_date=date.today() + timedelta(days=21),
        )
    )
    with pytest.raises(IntegrityError):
        test_db.commit()


def test_calculate_nights(test_db, setup_reservation_data):
    prop, rt, guest = setup_reservation_data
    res = make_res(
        prop,
        rt,
        guest,
        "CONF003",
        check_in_date=date(2024, 1, 15),
        check_out_date=date(2024, 1, 20),
    )
    assert res.calculate_nights() == 5
    assert res.number_of_nights == 5


def test_calculate_total_amount(test_db, setup_reservation_data):
    prop, rt, guest = setup_reservation_data
    res = make_res(
        prop,
        rt,
        guest,
        "CONF004",
        number_of_nights=4,
        nightly_rate=Decimal("125.50"),
        total_amount=Decimal("0"),
    )
    assert res.calculate_total_amount() == Decimal("502.00")


def test_full_lifecycle(test_db, setup_reservation_data):
    prop, rt, guest = setup_reservation_data
    res = make_res(prop, rt, guest, "CONF005")
    test_db.add(res)
    test_db.commit()

    assert res.status == ReservationStatus.PENDING
    assert res.confirm("receptionist") is True
    assert res.status == ReservationStatus.CONFIRMED
    assert res.confirmed_by == "receptionist"

    assert res.check_in() is True
    assert res.status == ReservationStatus.CHECKED_IN
    assert res.actual_arrival_time is not None

    assert res.check_out() is True
    assert res.status == ReservationStatus.CHECKED_OUT


def test_cancellation(test_db, setup_reservation_data):
    prop, rt, guest = setup_reservation_data
    res = make_res(prop, rt, guest, "CONF006", status=ReservationStatus.CONFIRMED)
    test_db.add(res)
    test_db.commit()

    assert res.cancel("guest", reason="Change of plans", fee=50) is True
    assert res.status == ReservationStatus.CANCELLED
    assert res.is_cancelled is True
    assert res.cancellation_reason == "Change of plans"
    assert res.cancellation_fee == Decimal("50")


def test_no_show(test_db, setup_reservation_data):
    prop, rt, guest = setup_reservation_data
    res = make_res(
        prop,
        rt,
        guest,
        "CONF007",
        check_in_date=date.today() - timedelta(days=2),
        check_out_date=date.today() - timedelta(days=1),
        number_of_nights=1,
        status=ReservationStatus.CONFIRMED,
    )
    test_db.add(res)
    test_db.commit()
    assert res.mark_no_show() is True
    assert res.status == ReservationStatus.NO_SHOW


def test_date_properties_future(test_db, setup_reservation_data):
    prop, rt, guest = setup_reservation_data
    res = make_res(prop, rt, guest, "CONF008")
    assert res.is_future is True
    assert res.is_past is False
    assert res.is_current is False


def test_date_properties_past(test_db, setup_reservation_data):
    prop, rt, guest = setup_reservation_data
    res = make_res(
        prop,
        rt,
        guest,
        "CONF009",
        check_in_date=date.today() - timedelta(days=10),
        check_out_date=date.today() - timedelta(days=7),
    )
    assert res.is_past is True
    assert res.is_future is False


def test_date_properties_current(test_db, setup_reservation_data):
    prop, rt, guest = setup_reservation_data
    res = make_res(
        prop,
        rt,
        guest,
        "CONF010",
        check_in_date=date.today() - timedelta(days=1),
        check_out_date=date.today() + timedelta(days=2),
    )
    assert res.is_current is True


def test_arriving_departing_today(test_db, setup_reservation_data):
    prop, rt, guest = setup_reservation_data
    arriving = make_res(
        prop,
        rt,
        guest,
        "CONF011",
        check_in_date=date.today(),
        check_out_date=date.today() + timedelta(days=2),
    )
    departing = make_res(
        prop,
        rt,
        guest,
        "CONF012",
        check_in_date=date.today() - timedelta(days=2),
        check_out_date=date.today(),
    )
    assert arriving.is_arriving_today is True
    assert departing.is_departing_today is True


def test_relationships(test_db, setup_reservation_data):
    prop, rt, guest = setup_reservation_data
    res = make_res(
        prop,
        rt,
        guest,
        "CONF013",
        check_in_date=date.today(),
        check_out_date=date.today() + timedelta(days=1),
    )
    test_db.add(res)
    test_db.commit()
    test_db.refresh(res)
    assert res.hotel_property.name == "Test Hotel"
    assert res.guest.full_name == "John Doe"
    assert res.room_type.name == "Standard Room"


def test_to_dict(test_db, setup_reservation_data):
    prop, rt, guest = setup_reservation_data
    res = make_res(
        prop,
        rt,
        guest,
        "CONF014",
        check_in_date=date.today() + timedelta(days=1),
        check_out_date=date.today() + timedelta(days=3),
        number_of_nights=2,
        nightly_rate=Decimal("150"),
        total_amount=Decimal("300"),
        status=ReservationStatus.CONFIRMED,
    )
    test_db.add(res)
    test_db.commit()
    d = res.to_dict()
    assert d["status"] == "confirmed"
    assert d["total_amount"] == 300.0


def test_cancel_blocked_for_checked_out(test_db, setup_reservation_data):
    prop, rt, guest = setup_reservation_data
    res = make_res(prop, rt, guest, "CONF015", status=ReservationStatus.CHECKED_OUT)
    test_db.add(res)
    test_db.commit()
    assert res.cancel("staff") is False


def test_confirm_blocked_for_non_pending(test_db, setup_reservation_data):
    prop, rt, guest = setup_reservation_data
    res = make_res(prop, rt, guest, "CONF016", status=ReservationStatus.CANCELLED)
    test_db.add(res)
    test_db.commit()
    assert res.confirm("staff") is False


def test_check_in_requires_confirmed(test_db, setup_reservation_data):
    prop, rt, guest = setup_reservation_data
    res = make_res(prop, rt, guest, "CONF017", status=ReservationStatus.PENDING)
    test_db.add(res)
    test_db.commit()
    assert res.check_in() is False


def test_check_out_requires_checked_in(test_db, setup_reservation_data):
    prop, rt, guest = setup_reservation_data
    res = make_res(prop, rt, guest, "CONF018", status=ReservationStatus.CONFIRMED)
    test_db.add(res)
    test_db.commit()
    assert res.check_out() is False


def test_no_show_blocked_for_future(test_db, setup_reservation_data):
    prop, rt, guest = setup_reservation_data
    res = make_res(prop, rt, guest, "CONF019", status=ReservationStatus.CONFIRMED)
    test_db.add(res)
    test_db.commit()
    assert res.mark_no_show() is False


def test_special_fields(test_db, setup_reservation_data):
    prop, rt, guest = setup_reservation_data
    res = make_res(
        prop,
        rt,
        guest,
        "CONF020",
        special_requests="High floor",
        internal_notes="VIP",
        guarantee_type="credit_card",
        credit_card_last_4="4242",
        estimated_arrival_time="15:00",
    )
    test_db.add(res)
    test_db.commit()
    test_db.refresh(res)
    assert res.special_requests == "High floor"
    assert res.credit_card_last_4 == "4242"


def test_default_source(test_db, setup_reservation_data):
    prop, rt, guest = setup_reservation_data
    res = make_res(prop, rt, guest, "CONF021")
    test_db.add(res)
    test_db.commit()
    assert res.source == ReservationSource.DIRECT


def test_ota_source_and_promo(test_db, setup_reservation_data):
    prop, rt, guest = setup_reservation_data
    res = make_res(
        prop, rt, guest, "CONF022", source=ReservationSource.OTA, promo_code="SUMMER10"
    )
    test_db.add(res)
    test_db.commit()
    assert res.source == ReservationSource.OTA
    assert res.promo_code == "SUMMER10"
