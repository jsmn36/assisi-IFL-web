import pytest
from uuid import uuid4
from datetime import datetime
import json
import requests_mock
from app.cm.gates.forwarding_gate import ForwardingGate
from app.cm.models import ExternalEvent, ChannelMapping
from app.cm.database import get_cm_db


@pytest.fixture
def mock_cm_db(mocker):
    # Mocking the CM database connection is crucial to avoid side effects
    mock_db = mocker.MagicMock()
    mock_session = mocker.MagicMock()
    mock_session.__enter__.return_value = mock_db
    mocker.patch("app.cm.gates.forwarding_gate.get_cm_db", return_value=mock_session)
    return mock_db


def test_forwarding_gate_event_not_found(mock_cm_db):
    mock_cm_db.query().filter().first.return_value = None
    gate = ForwardingGate()
    result = gate.execute(uuid4())
    assert result.success is False
    assert result.error_code == "NOT_FOUND"


def test_forwarding_gate_invalid_state(mock_cm_db):
    event = ExternalEvent(status="processing")
    mock_cm_db.query().filter().first.return_value = event
    gate = ForwardingGate()
    result = gate.execute(uuid4())
    assert result.success is False
    assert result.error_code == "INVALID_STATE"


def test_forwarding_gate_unmapped_room(mock_cm_db):
    event = ExternalEvent(
        status="validated",
        property_id=uuid4(),
        channel="booking_com",
        raw_payload={"room_type": "unmapped_room"},
    )
    mock_cm_db.query().filter().first.side_effect = [
        event,
        None,
    ]  # event found, mapping not found

    gate = ForwardingGate()
    result = gate.execute(uuid4())
    assert result.success is False
    assert result.error_code == "UNMAPPED_ROOM_TYPE"


def test_forwarding_gate_success(mock_cm_db, requests_mock):
    event_id = uuid4()
    prop_id = uuid4()

    event = ExternalEvent(
        event_id=event_id,
        status="validated",
        property_id=prop_id,
        channel="booking_com",
        external_reference="BKG-123",
        raw_payload={
            "room_type": "mapped_room",
            "guest_name": "Test Guest",
            "check_in": "2026-03-20",
            "check_out": "2026-03-22",
            "guests": 2,
        },
    )
    mapping = ChannelMapping(pms_room_type_id=5)

    # Mocking sequential query results
    mock_cm_db.query().filter().first.side_effect = [event, mapping]

    # Mock PM server endpoint
    pms_response = {
        "success": True,
        "reservation_id": 456,
        "confirmation_code": "RES-XYZ",
    }
    requests_mock.post(
        "http://localhost:8000/api/v1/pms/integration/ingest", json=pms_response
    )

    gate = ForwardingGate()
    result = gate.execute(event_id)

    assert result.success is True
    assert event.status == "processed"
    assert event.pms_verdict == pms_response
    assert event.correlation_id is not None
