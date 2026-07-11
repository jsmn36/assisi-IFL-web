import pytest
import uuid
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_admin_create_mapping_and_read(test_db):
    property_id = str(uuid.uuid4())
    req_payload = {
        "channel": "booking_com",
        "property_id": property_id,
        "room_type_id": 5,
        "channel_room_id": "test_ota_rm_1",
    }

    # Create mapping
    create_resp = client.post("/cm/admin/mappings", json=req_payload)
    if create_resp.status_code == 422:
        print("422 detail:", create_resp.json())
    assert create_resp.status_code == 200
    mapping_id = create_resp.json()["mapping_id"]

    # Read mapping
    read_resp = client.get(f"/cm/admin/mappings?property_id={property_id}")
    assert read_resp.status_code == 200
    mappings = read_resp.json()
    assert len(mappings) >= 1

    found = next((m for m in mappings if m["mapping_id"] == mapping_id), None)
    assert found is not None
    assert found["channel"] == "booking_com"
    assert found["channel_room_id"] == "test_ota_rm_1"
    assert found["room_type_id"] == 5


def test_admin_delete_mapping(test_db):
    property_id = str(uuid.uuid4())
    req_payload = {
        "channel": "generic",
        "property_id": property_id,
        "room_type_id": 10,
        "channel_room_id": "generic_rm_1",
    }

    # Create mapping
    create_resp = client.post("/cm/admin/mappings", json=req_payload)
    assert create_resp.status_code == 200
    mapping_id = create_resp.json()["mapping_id"]

    # Delete mapping
    del_resp = client.delete(f"/cm/admin/mappings/{mapping_id}")
    assert del_resp.status_code == 200

    # Verify it is deleted
    read_resp = client.get(f"/cm/admin/mappings?property_id={property_id}")
    mappings = read_resp.json()
    found = next((m for m in mappings if m["mapping_id"] == mapping_id), None)
    assert found is None
