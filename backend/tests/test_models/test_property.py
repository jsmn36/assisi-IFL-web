"""
Test Property Model
"""
import pytest
from app.models.property import Property
from sqlalchemy.exc import IntegrityError


def test_create_property(test_db):
    """Test creating a property"""
    property = Property(
        name="Grand Hotel",
        code="GRAND001",
        address_line1="123 Main Street",
        city="New York",
        state="NY",
        country="USA",
        postal_code="10001",
        phone="+1-212-555-0100",
        email="info@grandhotel.com",
        timezone="America/New_York",
        currency="USD",
    )

    test_db.add(property)
    test_db.commit()
    test_db.refresh(property)

    assert property.id is not None
    assert property.name == "Grand Hotel"
    assert property.code == "GRAND001"
    assert property.is_active is True
    assert property.created_at is not None


def test_property_code_unique(test_db):
    """Test that property code must be unique"""
    property1 = Property(
        name="Hotel A",
        code="HOTEL001",
        address_line1="123 Main St",
        city="New York",
        state="NY",
        postal_code="10001",
    )
    test_db.add(property1)
    test_db.commit()

    property2 = Property(
        name="Hotel B",
        code="HOTEL001",
        address_line1="456 Oak Ave",
        city="Boston",
        state="MA",
        postal_code="02101",
    )
    test_db.add(property2)

    with pytest.raises(IntegrityError):
        test_db.commit()


def test_property_to_dict(test_db):
    """Test property to_dict method"""
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

    property_dict = property.to_dict()

    assert property_dict["name"] == "Test Hotel"
    assert property_dict["code"] == "TEST001"
    assert "created_at" in property_dict
