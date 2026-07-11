import pytest
from app.models import Property, RoomType, Room
from decimal import Decimal


def test_get_available_rooms(client, test_db):
    # Setup
    prop = Property(
        name="Test",
        code="TROOM1",
        address_line1="1",
        city="C",
        state="S",
        postal_code="1",
    )
    test_db.add(prop)
    test_db.commit()
    test_db.refresh(prop)

    rt = RoomType(
        property_id=prop.id, code="STD", name="Std", base_price=Decimal("100")
    )
    test_db.add(rt)
    test_db.commit()
    test_db.refresh(rt)

    room = Room(
        property_id=prop.id, room_type_id=rt.id, room_number="101", status="available"
    )
    test_db.add(room)
    test_db.commit()

    # Test
    response = client.get(f"/api/v1/rooms/available?property_id={prop.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["room_number"] == "101"


def test_mark_room_clean(client, test_db, auth_headers):
    # Setup
    prop = Property(
        name="Test", code="T2", address_line1="1", city="C", state="S", postal_code="1"
    )
    test_db.add(prop)
    test_db.commit()
    test_db.refresh(prop)

    rt = RoomType(
        property_id=prop.id, code="STD2", name="Std", base_price=Decimal("100")
    )
    test_db.add(rt)
    test_db.commit()
    test_db.refresh(rt)

    room = Room(property_id=prop.id, room_type_id=rt.id, room_number="102")
    test_db.add(room)
    test_db.commit()

    # Test
    response = client.post(f"/api/v1/rooms/{room.id}/clean", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
