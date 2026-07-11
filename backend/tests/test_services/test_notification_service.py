"""
Test Notification Service
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from app.services.notification_service import NotificationService
from app.models import Property, RoomType, Room, Guest, Reservation
from app.models.notification import Notification, NotificationType, NotificationStatus


@pytest.fixture
def setup_notification_test_data(test_db):
    property = Property(
        name="Notification Hotel",
        code="NOTIF",
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
        max_occupancy=2,
        max_adults=2,
        max_children=1,
    )
    test_db.add(room_type)
    test_db.commit()

    room = Room(property_id=property.id, room_type_id=room_type.id, room_number="101")
    test_db.add(room)
    test_db.commit()

    guest = Guest(first_name="Test", last_name="Guest", email="test@notifications.com")
    test_db.add(guest)
    test_db.commit()

    reservation = Reservation(
        property_id=property.id,
        guest_id=guest.id,
        room_type_id=room_type.id,
        confirmation_number="NOTIF-001",
        check_in_date=date.today() + timedelta(days=1),
        check_out_date=date.today() + timedelta(days=3),
        number_of_nights=2,
        num_adults=2,
        nightly_rate=Decimal("100"),
        total_amount=Decimal("200"),
    )
    test_db.add(reservation)
    test_db.commit()

    return property, room_type, room, guest, reservation


def test_get_notification_history(test_db, setup_notification_test_data):
    """Test getting notification history"""
    property, room_type, room, guest, reservation = setup_notification_test_data

    notification1 = Notification(
        type=NotificationType.EMAIL,
        status=NotificationStatus.SENT,
        recipient_email=guest.email,
        guest_id=guest.id,
        reservation_id=reservation.id,
        subject="Test 1",
        message="",
        template_name="test",
    )
    notification2 = Notification(
        type=NotificationType.EMAIL,
        status=NotificationStatus.PENDING,
        recipient_email=guest.email,
        guest_id=guest.id,
        subject="Test 2",
        message="",
        template_name="test",
    )
    test_db.add_all([notification1, notification2])
    test_db.commit()

    service = NotificationService(test_db)

    history = service.get_notification_history(guest_id=guest.id)
    assert len(history) == 2

    history = service.get_notification_history(reservation_id=reservation.id)
    assert len(history) == 1


def test_notification_model_creation(test_db, setup_notification_test_data):
    """Test notification model"""
    property, room_type, room, guest, reservation = setup_notification_test_data

    notification = Notification(
        type=NotificationType.EMAIL,
        status=NotificationStatus.PENDING,
        recipient_email=guest.email,
        guest_id=guest.id,
        reservation_id=reservation.id,
        subject="Test Notification",
        message="Test message",
        template_name="test_template",
    )
    test_db.add(notification)
    test_db.commit()

    saved = (
        test_db.query(Notification).filter(Notification.guest_id == guest.id).first()
    )

    assert saved is not None
    assert saved.type == NotificationType.EMAIL
    assert saved.status == NotificationStatus.PENDING
    assert saved.recipient_email == guest.email
