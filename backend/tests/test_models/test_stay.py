import pytest
from app.models import Property, RoomType, Room, Guest, Reservation, Stay
from app.models import ReservationStatus, StayStatus
from datetime import date, timedelta
from decimal import Decimal


@pytest.fixture
def setup_stay_data(test_db):
    """Create all dependencies for stay tests"""

    # Property
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
    test_db.refresh(prop)

    # Room Type
    room_type = RoomType(
        property_id=prop.id,
        code="STD",
        name="Standard Room",
        base_price=Decimal("99.99"),
    )
    test_db.add(room_type)
    test_db.commit()
    test_db.refresh(room_type)

    # Room
    room = Room(property_id=prop.id, room_type_id=room_type.id, room_number="101")
    test_db.add(room)
    test_db.commit()
    test_db.refresh(room)

    # Guest
    guest = Guest(first_name="Jane", last_name="Smith", email="jane.smith@example.com")
    test_db.add(guest)
    test_db.commit()
    test_db.refresh(guest)

    # Reservation
    reservation = Reservation(
        property_id=prop.id,
        guest_id=guest.id,
        room_type_id=room_type.id,
        confirmation_number="STAY001",
        check_in_date=date.today(),
        check_out_date=date.today() + timedelta(days=3),
        number_of_nights=3,
        nightly_rate=Decimal("129.99"),
        total_amount=Decimal("389.97"),
        status=ReservationStatus.CONFIRMED,
    )
    test_db.add(reservation)
    test_db.commit()
    test_db.refresh(reservation)

    return prop, room, guest, reservation


def test_create_stay(test_db, setup_stay_data):
    """Test creating a stay"""
    prop, room, guest, reservation = setup_stay_data

    stay = Stay(
        property_id=prop.id,
        reservation_id=reservation.id,
        guest_id=guest.id,
        room_id=room.id,
        check_in_date=date.today(),
        check_out_date=date.today() + timedelta(days=3),
        num_adults=2,
        nightly_rate=Decimal("129.99"),
    )

    test_db.add(stay)
    test_db.commit()
    test_db.refresh(stay)

    assert stay.id is not None
    assert stay.status == StayStatus.RESERVED
    assert stay.number_of_nights == 3
    assert stay.is_active is False


def test_stay_check_in_workflow(test_db, setup_stay_data):
    """Test check-in workflow"""
    prop, room, guest, reservation = setup_stay_data

    stay = Stay(
        property_id=prop.id,
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

    assert stay.status == StayStatus.RESERVED

    result = stay.check_in(checked_in_by="receptionist")
    test_db.commit()
    test_db.refresh(stay)

    assert result is True
    assert stay.status == StayStatus.CHECKED_IN
    assert stay.actual_check_in_time is not None
    assert stay.checked_in_by == "receptionist"


def test_stay_check_out_workflow(test_db, setup_stay_data):
    """Test check-out workflow"""
    prop, room, guest, reservation = setup_stay_data

    stay = Stay(
        property_id=prop.id,
        reservation_id=reservation.id,
        guest_id=guest.id,
        room_id=room.id,
        check_in_date=date.today(),
        check_out_date=date.today() + timedelta(days=1),
        nightly_rate=Decimal("100"),
        status=StayStatus.CHECKED_IN,
    )
    test_db.add(stay)
    test_db.commit()
    test_db.refresh(stay)

    result = stay.check_out(checked_out_by="receptionist")
    test_db.commit()
    test_db.refresh(stay)

    assert result is True
    assert stay.status == StayStatus.CHECKED_OUT
    assert stay.requires_cleaning is True


def test_stay_charge_tracking(test_db, setup_stay_data):
    """Test tracking charges"""
    prop, room, guest, reservation = setup_stay_data

    stay = Stay(
        property_id=prop.id,
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

    stay.add_room_charge(Decimal("100"))
    stay.add_room_charge(Decimal("100"))
    stay.add_other_charge(Decimal("25"))
    stay.add_other_charge(Decimal("50"))

    assert stay.total_room_charges == Decimal("200")
    assert stay.total_other_charges == Decimal("75")
    assert stay.total_charges == Decimal("275")


def test_stay_cancellation(test_db, setup_stay_data):
    """Test cancelling a stay"""
    prop, room, guest, reservation = setup_stay_data

    stay = Stay(
        property_id=prop.id,
        reservation_id=reservation.id,
        guest_id=guest.id,
        room_id=room.id,
        check_in_date=date.today() + timedelta(days=7),
        check_out_date=date.today() + timedelta(days=9),
        nightly_rate=Decimal("100"),
    )
    test_db.add(stay)
    test_db.commit()
    test_db.refresh(stay)

    result = stay.cancel()
    assert result is True
    assert stay.status == StayStatus.CANCELLED


def test_stay_housekeeping_flags(test_db, setup_stay_data):
    """Test housekeeping flags"""
    prop, room, guest, reservation = setup_stay_data

    stay = Stay(
        property_id=prop.id,
        reservation_id=reservation.id,
        guest_id=guest.id,
        room_id=room.id,
        check_in_date=date.today(),
        check_out_date=date.today() + timedelta(days=1),
        nightly_rate=Decimal("100"),
    )
    test_db.add(stay)
    test_db.commit()
    test_db.refresh(stay)

    assert stay.requires_cleaning is True

    stay.mark_cleaning_completed()
    test_db.commit()
    test_db.refresh(stay)

    assert stay.cleaning_completed is True
    assert stay.requires_cleaning is False


def test_stay_relationships(test_db, setup_stay_data):
    """Test stay relationships"""
    prop, room, guest, reservation = setup_stay_data

    stay = Stay(
        property_id=prop.id,
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

    assert stay.prop.name == "Test Hotel"
    assert stay.reservation.confirmation_number == "STAY001"
    assert stay.room.room_number == "101"

    test_db.refresh(reservation)
    assert len(reservation.stays) == 1


def test_stay_to_dict(test_db, setup_stay_data):
    """Test to_dict method"""
    prop, room, guest, reservation = setup_stay_data

    stay = Stay(
        property_id=prop.id,
        reservation_id=reservation.id,
        guest_id=guest.id,
        room_id=room.id,
        check_in_date=date.today(),
        check_out_date=date.today() + timedelta(days=3),
        nightly_rate=Decimal("125.00"),
        num_adults=2,
        num_children=1,
    )
    test_db.add(stay)
    test_db.commit()
    test_db.refresh(stay)

    stay_dict = stay.to_dict()

    assert stay_dict["room_id"] == room.id
    assert stay_dict["reservation_id"] == reservation.id
    assert stay_dict["status"] == "reserved"
    assert stay_dict["number_of_nights"] == 3
    assert stay_dict["nightly_rate"] == 125.00
    assert stay_dict["num_adults"] == 2
    assert stay_dict["num_children"] == 1


def test_stay_validate_dates_raises_for_bad_checkout():
    """validate_dates should reject check_out_date before or equal to check_in_date."""
    base_kwargs = dict(
        property_id=1,
        reservation_id=1,
        guest_id=1,
        room_id=1,
        check_in_date=date.today(),
        check_out_date=date.today() + timedelta(days=1),
        nightly_rate=Decimal("100.00"),
    )
    stay = Stay(**base_kwargs)

    # Setting an earlier/equal check_out_date should raise
    with pytest.raises(ValueError):
        stay.check_out_date = date.today()


def test_stay_validate_dates_raises_for_bad_checkin():
    """validate_dates should reject check_in_date after or equal to check_out_date."""
    base_kwargs = dict(
        property_id=1,
        reservation_id=1,
        guest_id=1,
        room_id=1,
        check_in_date=date.today(),
        check_out_date=date.today() + timedelta(days=1),
        nightly_rate=Decimal("100.00"),
    )
    stay = Stay(**base_kwargs)

    with pytest.raises(ValueError):
        stay.check_in_date = date.today() + timedelta(days=2)


def test_stay_number_of_nights_zero_when_dates_missing():
    """number_of_nights should be 0 when either date is missing."""
    stay = Stay(
        property_id=1,
        reservation_id=1,
        guest_id=1,
        room_id=1,
        nightly_rate=Decimal("100.00"),
    )
    # No dates set -> falls back to 0
    assert stay.number_of_nights == 0


def test_stay_check_in_out_and_cancel_failure_paths():
    """Exercise False branches of check_in, check_out and cancel."""
    base_kwargs = dict(
        property_id=1,
        reservation_id=1,
        guest_id=1,
        room_id=1,
        check_in_date=date.today(),
        check_out_date=date.today() + timedelta(days=1),
        nightly_rate=Decimal("100.00"),
    )

    # check_in should return False when not RESERVED
    stay_checked_in = Stay(status=StayStatus.CHECKED_IN, **base_kwargs)
    assert stay_checked_in.check_in("user") is False

    # check_out should return False when not CHECKED_IN
    stay_reserved = Stay(status=StayStatus.RESERVED, **base_kwargs)
    assert stay_reserved.check_out("user") is False

    # cancel should return False when not RESERVED
    stay_cancelled = Stay(status=StayStatus.CHECKED_IN, **base_kwargs)
    assert stay_cancelled.cancel() is False


def test_stay_mark_cleaning_required_and_completed():
    """mark_cleaning_required and mark_cleaning_completed should toggle flags correctly."""
    stay = Stay(
        property_id=1,
        reservation_id=1,
        guest_id=1,
        room_id=1,
        check_in_date=date.today(),
        check_out_date=date.today() + timedelta(days=1),
        nightly_rate=Decimal("100.00"),
        requires_cleaning=False,
        cleaning_completed=True,
    )

    stay.mark_cleaning_required()
    assert stay.requires_cleaning is True
    assert stay.cleaning_completed is False

    stay.mark_cleaning_completed()
    assert stay.cleaning_completed is True
    assert stay.requires_cleaning is False


def test_stay_repr_uses_status_value():
    """__repr__ should include the status value without crashing."""
    stay = Stay(
        property_id=1,
        reservation_id=1,
        guest_id=1,
        room_id=1,
        check_in_date=date.today(),
        check_out_date=date.today() + timedelta(days=1),
        nightly_rate=Decimal("100.00"),
        status=StayStatus.RESERVED,
    )
    repr_text = repr(stay)
    assert "status=reserved" in repr_text
