"""
Test RoomService
"""
import pytest
from app.services.room_service import RoomService
from app.services.base_service import BusinessRuleError
from app.models import Property, RoomType, Room, OccupancyState, ConditionState
from datetime import date, timedelta
from decimal import Decimal


@pytest.fixture
def setup_room_service_data(test_db):
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

    room1 = Room(property_id=property.id, room_type_id=room_type.id, room_number="101")
    room2 = Room(property_id=property.id, room_type_id=room_type.id, room_number="102")
    test_db.add_all([room1, room2])
    test_db.commit()

    return property, room_type, room1, room2


def test_get_room_by_number(test_db, setup_room_service_data):
    """Test getting room by number"""
    property, room_type, room1, room2 = setup_room_service_data

    service = RoomService(test_db)
    room = service.get_room(room_number="101", property_id=property.id)

    assert room.room_number == "101"


def test_get_available_rooms(test_db, setup_room_service_data):
    """Test getting available rooms"""
    property, room_type, room1, room2 = setup_room_service_data

    service = RoomService(test_db)
    available = service.get_available_rooms(property_id=property.id)

    assert len(available) == 2  # Both rooms available


def test_mark_room_clean(test_db, setup_room_service_data):
    """Test marking room as clean"""
    property, room_type, room1, room2 = setup_room_service_data

    # Mark dirty first
    room1.mark_dirty()
    test_db.commit()

    service = RoomService(test_db)
    cleaned = service.mark_room_clean(room1.id, "housekeeper")

    assert cleaned.condition_state == ConditionState.CLEAN


def test_take_room_out_of_order(test_db, setup_room_service_data):
    """Test taking room out of order"""
    property, room_type, room1, room2 = setup_room_service_data

    service = RoomService(test_db)
    ooo = service.take_room_out_of_order(room1.id, "Maintenance required", "manager")

    assert ooo.occupancy_state == OccupancyState.OUT_OF_ORDER
    assert not ooo.is_available()


def test_return_room_to_service(test_db, setup_room_service_data):
    """Test returning room to service"""
    property, room_type, room1, room2 = setup_room_service_data

    service = RoomService(test_db)
    service.take_room_out_of_order(room1.id, "Maintenance", "manager")

    returned = service.return_room_to_service(room1.id, "manager")

    assert returned.occupancy_state == OccupancyState.VACANT
    assert returned.is_available()


def test_housekeeping_status(test_db, setup_room_service_data):
    """Test getting housekeeping status"""
    property, room_type, room1, room2 = setup_room_service_data

    service = RoomService(test_db)
    status = service.get_housekeeping_status(property.id)

    assert status["total"] == 2
    assert status["vacant_clean"] == 2
    assert status["available"] == 2
