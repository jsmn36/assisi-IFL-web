import pytest
import uuid
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)


@patch("app.cm.api.webhooks.InboundIngestionGate")
def test_post_webhook_booking_com_success(mock_gate, test_db):
    mock_instance = mock_gate.return_value
    mock_instance.execute.return_value = MagicMock(
        success=True, event_id=uuid.uuid4(), message="Accepted"
    )

    payload = {
        "reservation_id": "BKG-123456789",
        "property_id": "123e4567-e89b-12d3-a456-426614174000",
        "guest_name": "John Doe",
        "room_type": "standard_double",
        "check_in": "2026-03-20",
        "check_out": "2026-03-22",
        "guests": 2,
        "total_price": 199.00,
        "currency": "USD",
    }

    response = client.post(
        "/cm/webhooks/booking.com",
        json=payload,
        headers={"X-Channel-API-Key": "test-key"},
    )

    assert response.status_code == 202
    assert response.json()["status"] == "accepted"


@patch("app.cm.api.webhooks.InboundIngestionGate")
def test_post_webhook_booking_com_invalid_schema(mock_gate, test_db):
    mock_instance = mock_gate.return_value
    mock_instance.execute.return_value = MagicMock(
        success=False, error_code="INVALID_SCHEMA", message="Missing fields"
    )

    payload = {"invalid": "schema"}

    response = client.post(
        "/cm/webhooks/booking.com",
        json=payload,
        headers={"X-Channel-API-Key": "test-key"},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["status"] == "rejected"


@patch("app.cm.api.webhooks.InboundIngestionGate")
def test_post_webhook_generic_success(mock_gate, test_db):
    mock_instance = mock_gate.return_value
    mock_instance.execute.return_value = MagicMock(
        success=True, event_id=uuid.uuid4(), message="Accepted"
    )

    payload = {
        "reservation_id": "WEB-123",
        "property_id": "123e4567-e89b-12d3-a456-426614174000",
        "guest_name": "Jane Doe",
        "room_type": "standard_double",
        "check_in": "2026-03-20",
        "check_out": "2026-03-22",
        "guests": 2,
        "total_price": 199.00,
        "currency": "USD",
    }

    response = client.post(
        "/cm/webhooks/website", json=payload, headers={"X-Channel-API-Key": "test-key"}
    )

    assert response.status_code == 202
