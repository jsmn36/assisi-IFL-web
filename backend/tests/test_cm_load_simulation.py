import pytest
import uuid
import time
import concurrent.futures
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_cm_load_simulation():
    """
    Test Phase 21 Criteria: Load Testing (100 webhooks/min).
    We will simulate an intense burst of 100 webhook requests concurrently.
    The primary goal is to ensure the Inbound Ingestion Gate (which is I/O DB bound)
    handles the concurrent connections gracefully and all return 202 Accepted.
    Because we use TestClient, we are restricted by the test environment's concurrency threadcap,
    but this ensures DB locking and session management hold up.
    """

    # Pre-generate 100 unique payloads
    num_requests = 100
    property_id = str(uuid.uuid4())

    payloads = []
    for i in range(num_requests):
        payloads.append(
            {
                "reservation_id": f"LOAD-{i}",
                "property_id": property_id,
                "guest_name": f"Load Guest {i}",
                "room_type": "standard_double",
                "check_in": "2026-04-01",
                "check_out": "2026-04-05",
                "guests": 2,
                "total_price": 400.0,
                "currency": "USD",
            }
        )

    def send_webhook(payload):
        response = client.post(
            "/cm/webhooks/booking.com",
            json=payload,
            headers={"X-Channel-API-Key": "test-key"},
        )
        return response

    start_time = time.time()

    # Execute concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        responses = list(executor.map(send_webhook, payloads))

    duration = time.time() - start_time

    # Assertions
    assert len(responses) == num_requests

    success_count = sum(1 for r in responses if r.status_code == 202)
    assert (
        success_count == num_requests
    ), f"Only {success_count}/{num_requests} succeeded. First failure: {[r.json() for r in responses if r.status_code != 202][:1]}"

    # To meet 100 per minute, it should ideally process this batch in under 10-15 seconds local
    assert duration < 30.0, f"Load test was too slow: {duration} seconds"
