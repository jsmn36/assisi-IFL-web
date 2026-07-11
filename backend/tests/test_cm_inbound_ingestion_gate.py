import pytest
import uuid
import json
from app.cm.gates.inbound_ingestion import InboundIngestionGate
from app.cm.models import ExternalEvent
from app.cm.database import get_cm_db


@pytest.fixture
def mock_cm_db(mocker):
    mock_db = mocker.MagicMock()
    mock_session = mocker.MagicMock()
    mock_session.__enter__.return_value = mock_db
    mocker.patch("app.cm.gates.inbound_ingestion.get_cm_db", return_value=mock_session)
    return mock_db


def test_inbound_ingestion_gate_success(mock_cm_db):
    webhook_data = {
        "reservation_id": "BKG-12345",
        "property_id": str(uuid.uuid4()),
        "guest_name": "John Doe",
        "room_type": "standard",
        "check_in": "2026-03-20",
        "check_out": "2026-03-22",
        "guests": 2,
        "total_price": 199.00,
        "currency": "USD",
    }

    gate = InboundIngestionGate("booking_com")
    result = gate.execute(webhook_data, "test-key")

    assert result.success is True
    mock_cm_db.add.assert_called_once()
    mock_cm_db.commit.assert_called_once()
    mock_cm_db.refresh.assert_called_once()

    # Verify that what was added is an ExternalEvent
    added_event = mock_cm_db.add.call_args[0][0]
    assert isinstance(added_event, ExternalEvent)
    assert added_event.status == "pending"
    assert added_event.channel == "booking_com"
    assert added_event.external_reference == "BKG-12345"


def test_inbound_ingestion_gate_invalid_schema(mock_cm_db):
    # Missing required fields
    webhook_data = {
        "reservation_id": "BKG-12345",
    }

    gate = InboundIngestionGate("booking_com")
    result = gate.execute(webhook_data, "test-key")

    assert result.success is False
    assert result.error_code == "INVALID_SCHEMA"
    mock_cm_db.add.assert_not_called()


def test_inbound_ingestion_gate_authentication_failed(mock_cm_db):
    webhook_data = {
        "reservation_id": "BKG-12345",
        "property_id": str(uuid.uuid4()),
        "guest_name": "John Doe",
        "room_type": "standard",
        "check_in": "2026-03-20",
        "check_out": "2026-03-22",
        "guests": 2,
        "total_price": 199.00,
        "currency": "USD",
    }

    gate = InboundIngestionGate("booking_com")
    result = gate.execute(webhook_data, "wrong-key")

    assert result.success is False
    assert result.error_code == "AUTHENTICATION_FAILED"
    mock_cm_db.add.assert_not_called()
