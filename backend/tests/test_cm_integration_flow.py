import pytest
import uuid
import threading
import time
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.cm.models import ExternalEvent
from app.cm.database import get_cm_db

client = TestClient(app)


@patch("app.cm.gates.forwarding_gate.requests.post")
def test_double_booking_prevention_flow(mock_requests_post, test_db):
    """
    Test Phase 21 Criteria: Double booking prevention.
    Two simultaneous bookings for same room should result in ONE success, ONE rejection.
    This simulates two webhooks coming in concurrently for the same dates/property/room_type.
    """
    property_id = str(uuid.uuid4())

    # We will simulate the PMS (ReservationConfirmationGate) checking availability with locking.
    # Because we're mocking the external bound (PMS side) we will use a lock here to simulate the
    # db row-level lock `SELECT FOR UPDATE` effect internally.

    # The first one to acquire the lock 'succeeds' finding availability, the second one 'fails'.
    pms_lock = threading.Lock()
    rooms_available = 1

    def pms_propose_mock(*args, **kwargs):
        nonlocal rooms_available
        with pms_lock:
            if rooms_available > 0:
                rooms_available -= 1
                return MagicMock(
                    status_code=200,
                    json=lambda: {
                        "success": True,
                        "reservation_id": 123,
                        "confirmation_code": "DBL_PREV_1",
                    },
                )
            else:
                return MagicMock(
                    status_code=200,
                    json=lambda: {
                        "success": False,
                        "error_code": "NO_AVAILABILITY",
                        "message": "No rooms available",
                    },
                )

    mock_requests_post.side_effect = pms_propose_mock

    # Need a worker-like behavior: call forwarding gate directly instead of rq worker to simulate the async behavior in tests
    from app.cm.gates.intent_validation import IntentValidationGate
    from app.cm.gates.forwarding_gate import ForwardingGate
    from app.cm.gates.pms_verdict_gate import PMSVerdictGate
    from app.cm.models import ChannelMapping

    # Seed mapping
    with get_cm_db() as db:
        mapping = ChannelMapping(
            property_id=property_id,
            channel="booking_com",
            external_room_type_id="standard_double",
            pms_room_type_id=5,
        )
        db.add(mapping)
        db.commit()

    def process_webhook(reservation_id):
        payload = {
            "reservation_id": reservation_id,
            "property_id": property_id,
            "guest_name": "Test Guest",
            "room_type": "standard_double",
            "check_in": "2026-03-20",
            "check_out": "2026-03-22",
            "guests": 2,
            "total_price": 100.0,
            "currency": "USD",
        }

        # 1. Ingestion
        resp = client.post(
            "/cm/webhooks/booking.com",
            json=payload,
            headers={"X-Channel-API-Key": "test-key"},
        )
        assert resp.status_code == 202
        event_id = uuid.UUID(resp.json()["event_id"])

        # 2. Validation
        v_gate = IntentValidationGate()
        v_res = v_gate.execute(event_id)
        if not v_res.success:
            return v_res

        # 3. Forward to PMS (where the double booking check happens)
        f_gate = ForwardingGate()
        f_res = f_gate.execute(event_id)

        # 4. PMS Verdict
        if f_res.success is not None:
            pvt_gate = PMSVerdictGate()
            pvt_gate.execute(event_id)

        return f_res

    class ThreadWithReturnValue(threading.Thread):
        def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
            threading.Thread.__init__(self, group, target, name, args, kwargs)
            self._return = None

        def run(self):
            if self._target is not None:
                self._return = self._target(*self._args, **self._kwargs)

        def join(self, *args):
            threading.Thread.join(self, *args)
            return self._return

    thread1 = ThreadWithReturnValue(target=process_webhook, args=("BKG-001",))
    thread2 = ThreadWithReturnValue(target=process_webhook, args=("BKG-002",))

    thread1.start()
    thread2.start()

    res1 = thread1.join()
    res2 = thread2.join()

    # Exactly one should succeed, exactly one should fail due to NO_AVAILABILITY
    successes = [r for r in [res1, res2] if r.success]
    failures = [r for r in [res1, res2] if not r.success]

    assert len(successes) == 1
    assert len(failures) == 1

    assert (
        failures[0].error_code == "NO_AVAILABILITY"
        or failures[0].data.get("error_code") == "NO_AVAILABILITY"
    )
