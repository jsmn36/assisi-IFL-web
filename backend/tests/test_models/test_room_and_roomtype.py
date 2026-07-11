from app.models.room_type import RoomType
from app.models.room import Room, OccupancyState, ConditionState


def test_create_room_type(test_db):
    room_type = RoomType(
        name="Deluxe", description="Deluxe Room", base_price=200, max_occupancy=2
    )
    test_db.add(room_type)
    test_db.commit()
    test_db.refresh(room_type)

    assert room_type.id is not None
    assert room_type.name == "Deluxe"
    assert room_type.base_price == 200


def test_create_room(test_db):
    room_type = RoomType(name="Standard", base_price=100, max_occupancy=2)
    test_db.add(room_type)
    test_db.commit()

    room = Room(room_number="101", room_type_id=room_type.id)
    test_db.add(room)
    test_db.commit()
    test_db.refresh(room)

    assert room.id is not None
    assert room.room_number == "101"
    assert room.occupancy_state == OccupancyState.VACANT
    assert room.condition_state == ConditionState.CLEAN
