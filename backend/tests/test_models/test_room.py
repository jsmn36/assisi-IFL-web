"""
Test Room Model with Dual State
"""
import pytest
from app.models.property import Property
from app.models.room_type import RoomType
from app.models.room import Room, OccupancyState, ConditionState
from decimal import Decimal
from datetime import datetime


@pytest.fixture
def setup_property_and_room_type(test_db):
    """Create property and room type for tests"""
    property = Property(
        name="Test Hotel",
        code="TEST001",
        address_line1="123 Test St",
        city="Test City",
        state="TC",
        postal_code="12345",
    )
    test_db.add(property)
    test_db.commit()

    room_type = RoomType(
        property_id=property.id,
        code="STD",
        name="Standard Room",
        base_price=Decimal("99.99"),
    )
    test_db.add(room_type)
    test_db.commit()

    return property, room_type


def test_create_room(test_db, setup_property_and_room_type):
    """Test creating a room"""
    property, room_type = setup_property_and_room_type

    room = Room(
        property_id=property.id,
        room_type_id=room_type.id,
        room_number="101",
        floor=1,
        building="Main",
    )

    test_db.add(room)
    test_db.commit()
    test_db.refresh(room)

    assert room.id is not None
    assert room.room_number == "101"
    assert room.occupancy_state == OccupancyState.VACANT
    assert room.condition_state == ConditionState.CLEAN


def test_room_dual_state_defaults(test_db, setup_property_and_room_type):
    """Test that room defaults to VACANT and CLEAN"""
    property, room_type = setup_property_and_room_type

    room = Room(property_id=property.id, room_type_id=room_type.id, room_number="102")
    test_db.add(room)
    test_db.commit()

    assert room.occupancy_state == OccupancyState.VACANT
    assert room.condition_state == ConditionState.CLEAN


def test_room_is_available(test_db, setup_property_and_room_type):
    """Test room availability logic"""
    property, room_type = setup_property_and_room_type

    # Room that is vacant and clean = available
    room1 = Room(
        property_id=property.id,
        room_type_id=room_type.id,
        room_number="101",
        occupancy_state=OccupancyState.VACANT,
        condition_state=ConditionState.CLEAN,
    )
    assert room1.is_available() is True

    # Room that is occupied = NOT available
    room2 = Room(
        property_id=property.id,
        room_type_id=room_type.id,
        room_number="102",
        occupancy_state=OccupancyState.OCCUPIED,
        condition_state=ConditionState.CLEAN,
    )
    assert room2.is_available() is False

    # Room that is vacant but dirty = NOT available
    room3 = Room(
        property_id=property.id,
        room_type_id=room_type.id,
        room_number="103",
        occupancy_state=OccupancyState.VACANT,
        condition_state=ConditionState.DIRTY,
    )
    assert room3.is_available() is False


def test_room_check_in_out_flow(test_db, setup_property_and_room_type):
    """Test check-in and check-out flow"""
    property, room_type = setup_property_and_room_type

    room = Room(property_id=property.id, room_type_id=room_type.id, room_number="201")
    test_db.add(room)
    test_db.commit()

    # Initial state: vacant, clean
    assert room.occupancy_state == OccupancyState.VACANT
    assert room.condition_state == ConditionState.CLEAN
    assert room.is_available() is True

    # Check in
    room.check_in()
    test_db.commit()
    assert room.occupancy_state == OccupancyState.OCCUPIED
    assert room.is_available() is False
    assert room.occupancy_changed_at is not None

    # Check out (should mark vacant AND dirty)
    room.check_out()
    test_db.commit()
    assert room.occupancy_state == OccupancyState.VACANT
    assert room.condition_state == ConditionState.DIRTY
    assert room.is_available() is False  # Dirty room not available

    # Clean the room
    room.mark_clean()
    test_db.commit()
    assert room.condition_state == ConditionState.CLEAN
    assert room.is_available() is True  # Now available again


def test_room_out_of_order(test_db, setup_property_and_room_type):
    """Test taking room out of order"""
    property, room_type = setup_property_and_room_type

    room = Room(property_id=property.id, room_type_id=room_type.id, room_number="301")
    test_db.add(room)
    test_db.commit()

    # Take out of order
    room.take_out_of_order(notes="Broken AC")
    test_db.commit()

    assert room.occupancy_state == OccupancyState.OUT_OF_ORDER
    assert room.notes == "Broken AC"
    assert room.is_available() is False

    # Return to service
    room.return_to_service()
    test_db.commit()

    assert room.occupancy_state == OccupancyState.VACANT
    assert room.condition_state == ConditionState.CLEAN
    assert room.notes is None
    assert room.is_available() is True


def test_room_cleaning_workflow(test_db, setup_property_and_room_type):
    """Test housekeeping cleaning workflow"""
    property, room_type = setup_property_and_room_type

    room = Room(
        property_id=property.id,
        room_type_id=room_type.id,
        room_number="401",
        condition_state=ConditionState.DIRTY,
    )
    test_db.add(room)
    test_db.commit()

    # Mark as clean
    room.mark_clean()
    test_db.commit()
    assert room.condition_state == ConditionState.CLEAN
    assert room.condition_changed_at is not None

    # Mark as inspected
    room.mark_inspected()
    test_db.commit()
    assert room.condition_state == ConditionState.INSPECTED

    # Inspected rooms are available
    assert room.is_available() is True


def test_room_relationships(test_db, setup_property_and_room_type):
    """Test room relationships to property and room type"""
    property, room_type = setup_property_and_room_type

    room = Room(property_id=property.id, room_type_id=room_type.id, room_number="501")
    test_db.add(room)
    test_db.commit()

    # Test relationship to property
    assert room.property.id == property.id
    assert room.property.name == "Test Hotel"

    assert room.room_type.id == room_type.id
    assert room.room_type.name == "Standard Room"


def test_check_in_already_occupied(test_db, setup_property_and_room_type):
    property, room_type = setup_property_and_room_type
    room = Room(
        property_id=property.id,
        room_type_id=room_type.id,
        room_number="601",
        occupancy_state=OccupancyState.OCCUPIED,
    )
    test_db.add(room)
    test_db.commit()
    try:
        room.check_in()
        test_db.commit()
    except Exception:
        pass


def test_check_out_when_vacant(test_db, setup_property_and_room_type):
    property, room_type = setup_property_and_room_type
    room = Room(
        property_id=property.id,
        room_type_id=room_type.id,
        room_number="602",
        occupancy_state=OccupancyState.VACANT,
    )
    test_db.add(room)
    test_db.commit()
    try:
        room.check_out()
        test_db.commit()
    except Exception:
        pass


def test_mark_dirty(test_db, setup_property_and_room_type):
    property, room_type = setup_property_and_room_type
    room = Room(
        property_id=property.id,
        room_type_id=room_type.id,
        room_number="603",
        condition_state=ConditionState.CLEAN,
    )
    test_db.add(room)
    test_db.commit()
    room.mark_dirty()
    test_db.commit()
    assert room.condition_state == ConditionState.DIRTY
    assert room.is_available() is False


def test_room_out_of_order_blocks_availability(test_db, setup_property_and_room_type):
    property, room_type = setup_property_and_room_type
    room = Room(
        property_id=property.id,
        room_type_id=room_type.id,
        room_number="604",
        occupancy_state=OccupancyState.OUT_OF_ORDER,
        condition_state=ConditionState.CLEAN,
    )
    test_db.add(room)
    test_db.commit()
    assert room.is_available() is False


def test_room_inspected_state_available(test_db, setup_property_and_room_type):
    property, room_type = setup_property_and_room_type
    room = Room(
        property_id=property.id,
        room_type_id=room_type.id,
        room_number="605",
        occupancy_state=OccupancyState.VACANT,
        condition_state=ConditionState.INSPECTED,
    )
    test_db.add(room)
    test_db.commit()
    assert room.is_available() is True


def test_room_to_dict(test_db, setup_property_and_room_type):
    property, room_type = setup_property_and_room_type
    room = Room(
        property_id=property.id,
        room_type_id=room_type.id,
        room_number="606",
        floor=2,
        building="East Wing",
    )
    test_db.add(room)
    test_db.commit()
    d = room.to_dict()
    assert d["room_number"] == "606"
    assert "occupancy_state" in d
    assert "condition_state" in d


def test_full_lifecycle(test_db, setup_property_and_room_type):
    property, room_type = setup_property_and_room_type
    room = Room(property_id=property.id, room_type_id=room_type.id, room_number="700")
    test_db.add(room)
    test_db.commit()
    assert room.is_available() is True
    room.check_in()
    test_db.commit()
    assert room.occupancy_state == OccupancyState.OCCUPIED
    room.check_out()
    test_db.commit()
    assert room.occupancy_state == OccupancyState.VACANT
    assert room.condition_state == ConditionState.DIRTY
    room.mark_clean()
    test_db.commit()
    assert room.condition_state == ConditionState.CLEAN
    room.mark_inspected()
    test_db.commit()
    assert room.condition_state == ConditionState.INSPECTED
    assert room.is_available() is True
