import pytest
from datetime import date, timedelta
from decimal import Decimal
from app.models import Property, RoomType, Guest, Reservation


def test_create_reservation(client, test_db, auth_headers):
    # Setup
    prop = Property(
        name="Test Prop",
        code="TP",
        address_line1="123",
        city="C",
        state="S",
        postal_code="12345",
    )
    test_db.add(prop)
    test_db.commit()

    rt = RoomType(
        property_id=prop.id, code="STD", name="Standard", base_price=Decimal("100.00")
    )
    test_db.add(rt)
    test_db.commit()

    gst = Guest(
        first_name="API",
        last_name="Test",
        email="api@test.com",
        guest_type="INDIVIDUAL",
    )
    test_db.add(gst)
    test_db.commit()

    response = client.post(
        "/api/v1/reservations",
        json={
            "property_id": prop.id,
            "guest_id": gst.id,
            "room_type_id": rt.id,
            "check_in_date": str(date.today() + timedelta(days=1)),
            "check_out_date": str(date.today() + timedelta(days=3)),
            "num_adults": 2,
            "num_children": 0,
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert "confirmation_number" in data
    assert data["status"] == "pending"


def test_get_reservation(client, test_db):
    prop = Property(
        name="Test", code="T", address_line1="1", city="C", state="S", postal_code="1"
    )
    test_db.add(prop)
    test_db.commit()

    res = Reservation(
        property_id=prop.id,
        guest_id=1,
        room_type_id=1,
        confirmation_number="API-GET-001",
        check_in_date=date.today(),
        check_out_date=date.today() + timedelta(days=1),
        number_of_nights=1,
        num_adults=1,
        nightly_rate=Decimal("100"),
        total_amount=Decimal("100"),
        status="pending",
    )
    test_db.add(res)
    test_db.commit()

    response = client.get(f"/api/v1/reservations/{res.id}")
    assert response.status_code == 200
    assert response.json()["confirmation_number"] == "API-GET-001"
