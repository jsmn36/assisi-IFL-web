"""
Test ReservationService
"""
import pytest
from app.services.reservation_service import ReservationService
from app.services.base_service import ValidationError, BusinessRuleError
from app.models import Property, RoomType, Guest, Reservation, ReservationStatus
from datetime import date, timedelta
from decimal import Decimal


@pytest.fixture
def setup_service_data(test_db):
    property = Property(
        name="Test Hotel",
        code="TEST",
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
        max_occupancy=3,
        max_adults=2,
        max_children=2,
    )
    test_db.add(room_type)
    test_db.commit()

    guest = Guest(first_name="John", last_name="Doe", email="john@example.com")
    test_db.add(guest)
    test_db.commit()

    return property, room_type, guest


def test_create_reservation(test_db, setup_service_data):
    """Test creating a reservation"""
    property, room_type, guest = setup_service_data

    service = ReservationService(test_db)

    reservation = service.create_reservation(
        property_id=property.id,
        guest_id=guest.id,
        room_type_id=room_type.id,
        check_in_date=date.today() + timedelta(days=7),
        check_out_date=date.today() + timedelta(days=9),
        num_adults=2,
        num_children=0,
        nightly_rate=Decimal("100"),
        created_by="test_user",
    )

    assert reservation.id is not None
    assert reservation.confirmation_number.startswith("RES-")
    assert reservation.number_of_nights == 2
    assert reservation.total_amount == Decimal("200")
    assert reservation.status == ReservationStatus.PENDING


def test_create_reservation_invalid_dates(test_db, setup_service_data):
    """Test creating reservation with invalid dates fails"""
    property, room_type, guest = setup_service_data

    service = ReservationService(test_db)

    with pytest.raises(ValidationError) as exc:
        service.create_reservation(
            property_id=property.id,
            guest_id=guest.id,
            room_type_id=room_type.id,
            check_in_date=date.today(),
            check_out_date=date.today() - timedelta(days=1),  # Invalid!
            num_adults=2,
        )

    assert (
        "check-out" in str(exc.value).lower() and "check-in" in str(exc.value).lower()
    )


def test_confirm_reservation(test_db, setup_service_data):
    """Test confirming a reservation"""
    property, room_type, guest = setup_service_data
    service = ReservationService(test_db)

    # Create reservation
    reservation = service.create_reservation(
        property_id=property.id,
        guest_id=guest.id,
        room_type_id=room_type.id,
        check_in_date=date.today() + timedelta(days=1),
        check_out_date=date.today() + timedelta(days=3),
        num_adults=2,
    )

    # Confirm it
    confirmed = service.confirm_reservation(reservation.id, "receptionist")

    assert confirmed.status == ReservationStatus.CONFIRMED
    assert confirmed.confirmed_by == "receptionist"


def test_cancel_reservation(test_db, setup_service_data):
    """Test cancelling a reservation"""
    property, room_type, guest = setup_service_data
    service = ReservationService(test_db)

    # Create and confirm reservation
    reservation = service.create_reservation(
        property_id=property.id,
        guest_id=guest.id,
        room_type_id=room_type.id,
        check_in_date=date.today() + timedelta(days=7),
        check_out_date=date.today() + timedelta(days=9),
        num_adults=2,
    )
    service.confirm_reservation(reservation.id, "receptionist")

    # Cancel it
    cancelled = service.cancel_reservation(
        reservation.id, "guest", reason="Change of plans"
    )

    assert cancelled.status == ReservationStatus.CANCELLED
    assert cancelled.cancelled_by == "guest"


def test_modify_reservation(test_db, setup_service_data):
    """Test modifying a reservation"""
    property, room_type, guest = setup_service_data
    service = ReservationService(test_db)

    # Create reservation
    reservation = service.create_reservation(
        property_id=property.id,
        guest_id=guest.id,
        room_type_id=room_type.id,
        check_in_date=date.today() + timedelta(days=7),
        check_out_date=date.today() + timedelta(days=9),
        num_adults=2,
    )

    # Modify it
    modified = service.modify_reservation(
        reservation.id,
        check_out_date=date.today() + timedelta(days=10),  # One extra night
        num_children=1,
    )

    assert modified.number_of_nights == 3
    assert modified.num_children == 1


def test_get_reservation_by_confirmation(test_db, setup_service_data):
    """Test getting reservation by confirmation number"""
    property, room_type, guest = setup_service_data
    service = ReservationService(test_db)

    # Create reservation
    reservation = service.create_reservation(
        property_id=property.id,
        guest_id=guest.id,
        room_type_id=room_type.id,
        check_in_date=date.today() + timedelta(days=1),
        check_out_date=date.today() + timedelta(days=3),
        num_adults=2,
    )

    # Retrieve by confirmation number
    found = service.get_reservation(confirmation_number=reservation.confirmation_number)

    assert found.id == reservation.id
