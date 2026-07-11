import pytest
import uuid
from datetime import datetime
from pydantic import ValidationError

from app.cm.gates.intent_validation import IntentValidationGate
from app.cm.models import ExternalEvent, IdempotencyRecord
from app.cm.database import get_cm_db


@pytest.fixture
def mock_cm_db(mocker):
    mock_db = mocker.MagicMock()
    mock_session = mocker.MagicMock()
    mock_session.__enter__.return_value = mock_db
    mocker.patch("app.cm.gates.intent_validation.get_cm_db", return_value=mock_session)
    return mock_db


def test_intent_validation_gate_event_not_found(mock_cm_db):
    mock_cm_db.query().filter().first.return_value = None
    gate = IntentValidationGate()
    result = gate.execute(uuid.uuid4())

    assert result.success is False
    assert result.error_code == "NOT_FOUND"


def test_intent_validation_gate_duplicate_idempotency(mock_cm_db):
    event = ExternalEvent(
        event_id=uuid.uuid4(), idempotency_key="booking_com:BKG-123:hash"
    )
    existing_idempotency = IdempotencyRecord(entity_ref_id=uuid.uuid4())

    # Mocking two separate sequential calls to query().filter().first()
    # first call for event, second call for idempotency record
    mock_cm_db.query().filter().first.side_effect = [event, existing_idempotency]

    gate = IntentValidationGate()
    result = gate.execute(uuid.uuid4())

    assert result.success is False
    assert result.error_code == "DUPLICATE"


def test_intent_validation_gate_unsupported_channel(mock_cm_db):
    event = ExternalEvent(
        event_id=uuid.uuid4(),
        idempotency_key="unsupported:BKG-123:hash",
        channel="unsupported",
    )

    mock_cm_db.query().filter().first.side_effect = [event, None]

    gate = IntentValidationGate()
    result = gate.execute(uuid.uuid4())

    assert result.success is False
    assert result.error_code == "UNSUPPORTED_CHANNEL"


def test_intent_validation_gate_invalid_dates(mock_cm_db):
    event = ExternalEvent(
        event_id=uuid.uuid4(),
        idempotency_key="booking_com:BKG-123:hash",
        channel="booking_com",
        raw_payload={
            "reservation_id": "BKG-123",
            "property_id": str(uuid.uuid4()),
            "guest_name": "Test Guest",
            "room_type": "standard",
            "check_in": "2026-03-22",  # Invalid
            "check_out": "2026-03-20",  # Invalid
            "guests": 2,
            "total_price": 100,
            "currency": "USD",
        },
    )

    mock_cm_db.query().filter().first.side_effect = [event, None]

    gate = IntentValidationGate()
    result = gate.execute(uuid.uuid4())

    assert result.success is False
    assert result.error_code == "INVALID_DATES"


def test_intent_validation_gate_success(mock_cm_db, mocker):
    property_id = str(uuid.uuid4())
    event = ExternalEvent(
        event_id=uuid.uuid4(),
        idempotency_key="booking_com:BKG-123:hash",
        channel="booking_com",
        raw_payload={
            "reservation_id": "BKG-123",
            "property_id": property_id,
            "guest_name": "Test Guest",
            "room_type": "standard",
            "check_in": "2026-03-20",
            "check_out": "2026-03-22",
            "guests": 2,
            "total_price": 100,
            "currency": "USD",
        },
    )

    mock_cm_db.query().filter().first.side_effect = [event, None]

    gate = IntentValidationGate()
    result = gate.execute(uuid.uuid4())

    assert result.success is True
    assert event.status == "validated"
    mock_cm_db.execute.assert_called_once()
    mock_cm_db.commit.assert_called_once()
