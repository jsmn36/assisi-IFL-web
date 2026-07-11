import pytest
import uuid
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.cm.models import ExternalEvent, IdempotencyRecord
from app.cm.database import get_cm_db

client = TestClient(app)


@patch("app.cm.gates.forwarding_gate.requests.post")
def test_pms_failure_and_recovery_simulation(mock_requests_post, test_db):
    """
    Test Phase 21 Criteria: Failure simulation tests.
    Simulate a booking webhook coming in when the PMS is down (returns 500 or timeout).
    The CM should gracefully 'Fail Closed' for the forwarding but 'Fail Open' for ingestion (accepting the payload).
    Then, simulate the async retry succeeding.
    """

    # 1. Setup mock to fail on the first attempt (timeout) and succeed on the second
    def pm_mock(*args, **kwargs):
        pm_mock.call_count += 1
        if pm_mock.call_count == 1:
            import requests

            raise requests.Timeout("PMS is down")
        else:
            return MagicMock(
                status_code=200,
                json=lambda: {
                    "success": True,
                    "reservation_id": 999,
                    "confirmation_code": "RECOVERED",
                },
            )

    pm_mock.call_count = 0
    mock_requests_post.side_effect = pm_mock

    # Seed mapping
    property_id = str(uuid.uuid4())
    from app.cm.models import ChannelMapping

    with get_cm_db() as db:
        mapping = ChannelMapping(
            property_id=property_id,
            channel="booking_com",
            external_room_type_id="standard_double",
            pms_room_type_id=5,
        )
        db.add(mapping)
        db.commit()

    webhook_payload = {
        "reservation_id": "FAIL-REC-001",
        "property_id": property_id,
        "guest_name": "Resilient Guest",
        "room_type": "standard_double",
        "check_in": "2026-03-20",
        "check_out": "2026-03-22",
        "guests": 2,
        "total_price": 200.0,
        "currency": "USD",
    }

    # 1. Webhook Ingram (Fail Open)
    ingest_resp = client.post(
        "/cm/webhooks/booking.com",
        json=webhook_payload,
        headers={"X-Channel-API-Key": "test-key"},
    )
    assert ingest_resp.status_code == 202  # Accepted despite PMS being "down"
    event_id = uuid.UUID(ingest_resp.json()["event_id"])

    from app.cm.gates.intent_validation import IntentValidationGate
    from app.cm.gates.forwarding_gate import ForwardingGate

    # 2. Validation Gate
    v_gate = IntentValidationGate()
    v_res = v_gate.execute(event_id)
    assert v_res.success is True

    # 3. Forwarding Gate (First Attempt - PMS Down)
    f_gate = ForwardingGate()
    f_res1 = f_gate.execute(event_id)

    assert f_res1.success is False
    assert f_res1.error_code == "PMS_TIMEOUT"

    with get_cm_db() as db:
        event = (
            db.query(ExternalEvent).filter(ExternalEvent.event_id == event_id).first()
        )
        assert event.status == "failed"
        assert event.retry_count == 1

    # 4. Forwarding Gate (Second Attempt - Recovery/Retry via worker)
    # Reset status simulate worker picking it up
    with get_cm_db() as db:
        event = (
            db.query(ExternalEvent).filter(ExternalEvent.event_id == event_id).first()
        )
        event.status = "validated"  # Worker resets it to validated to retry
        db.commit()

    f_res2 = f_gate.execute(event_id)

    assert f_res2.success is True
    assert f_res2.data["confirmation_code"] == "RECOVERED"

    with get_cm_db() as db:
        event = (
            db.query(ExternalEvent).filter(ExternalEvent.event_id == event_id).first()
        )
        assert event.status == "processed"
        assert event.retry_count == 1  # Hasn't incremented because it succeeded
