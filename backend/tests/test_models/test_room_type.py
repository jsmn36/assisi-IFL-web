import pytest
from decimal import Decimal
from app.models.room_type import RoomType
from app.models.property import Property


def create_property(test_db):
    """
    Helper function to create a Property.
    Avoids repeating code in every test.
    """
    property = Property(name="Test Hotel", code="TEST")
    test_db.add(property)
    test_db.commit()
    test_db.refresh(property)
    return property


def test_room_type_to_dict(test_db):
    # 1️⃣ Create Property
    property = create_property(test_db)

    # 2️⃣ Create RoomType linked to Property
    room_type = RoomType(
        property_id=property.id,
        code="DLX",
        name="Deluxe",
        base_price=Decimal("199.99"),
        max_occupancy=2,
    )

    test_db.add(room_type)
    test_db.commit()
    test_db.refresh(room_type)

    d = room_type.to_dict()

    assert d["name"] == "Deluxe"
    assert d["code"] == "DLX"
    assert "base_price" in d
    assert d["property_id"] == property.id


def test_room_type_default_values(test_db):
    # 1️⃣ Create Property
    property = create_property(test_db)

    # 2️⃣ Create RoomType
    room_type = RoomType(
        property_id=property.id, code="ECO", name="Economy", base_price=Decimal("79.00")
    )

    test_db.add(room_type)
    test_db.commit()
    test_db.refresh(room_type)

    assert room_type.id is not None
    assert room_type.is_active is True
