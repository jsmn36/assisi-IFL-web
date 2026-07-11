import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)


@patch("app.cm.api.egress.ProjectionPublishGate")
def test_get_availability_success(mock_gate, test_db):
    mock_instance = mock_gate.return_value
    mock_instance.execute.return_value = MagicMock(
        success=True,
        data={"availability": [{"date": "2026-03-20", "available_rooms": 3}]},
    )

    response = client.get(
        "/cm/availability",
        params={
            "property_id": "123e4567-e89b-12d3-a456-426614174000",
            "room_type_id": 5,
            "start_date": "2026-03-20",
            "end_date": "2026-03-22",
        },
        headers={"X-Channel-API-Key": "test-key"},
    )

    assert response.status_code == 200
    assert "availability" in response.json()


@patch("app.cm.api.egress.ProjectionPublishGate")
def test_get_availability_gate_failure(mock_gate, test_db):
    mock_instance = mock_gate.return_value
    mock_instance.execute.return_value = MagicMock(
        success=False, error_code="PMS_FETCH_ERROR", message="Failed to connect"
    )

    response = client.get(
        "/cm/availability",
        params={
            "property_id": "123e4567-e89b-12d3-a456-426614174000",
            "room_type_id": 5,
            "start_date": "2026-03-20",
            "end_date": "2026-03-22",
        },
        headers={"X-Channel-API-Key": "test-key"},
    )

    # Standard behavior in egress.py right now is 'fail closed' = return empty availability on gate error
    assert response.status_code == 200
    assert len(response.json()["availability"]) == 0


@patch("app.cm.api.egress.ProjectionPublishGate")
def test_get_pricing_success(mock_gate, test_db):
    mock_instance = mock_gate.return_value
    mock_instance.execute.return_value = MagicMock(
        success=True, data={"rates": [{"date": "2026-03-20", "amount": 120.0}]}
    )

    response = client.get(
        "/cm/pricing",
        params={
            "property_id": "123e4567-e89b-12d3-a456-426614174000",
            "room_type_id": 5,
            "start_date": "2026-03-20",
            "end_date": "2026-03-22",
        },
        headers={"X-Channel-API-Key": "test-key"},
    )

    assert response.status_code == 200
    assert "pricing" in response.json()


def test_api_unauthorized(test_db):
    response = client.get(
        "/cm/availability",
        params={
            "property_id": "123e4567-e89b-12d3-a456-426614174000",
            "room_type_id": 5,
            "start_date": "2026-03-20",
            "end_date": "2026-03-22",
        },
    )
    assert response.status_code == 401
