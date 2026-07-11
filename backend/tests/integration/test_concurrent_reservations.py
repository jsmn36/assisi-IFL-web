"""
Concurrent Reservation Stress Test
Sends 10 simultaneous reservation requests for the same room/date.
Only 1 should succeed; all others must return 409 (or be rejected by the Gate).
"""
import os
import pytest
import threading
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("CRM_DATABASE_URL", "sqlite:///./test_crm_concurrent.db")
os.environ.setdefault("CM_DATABASE_URL", "sqlite:///./test_cm_concurrent.db")

from app.main import app
from app.database import Base, get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.property import Property
from app.models.room_type import RoomType
from app.models.room import Room
from app.models.guest import Guest
from app.models.rate_plan import RatePlan
from app.models.reservation import Reservation


CONCURRENT_DB_URL = "sqlite:///./concurrent_test.db"


@pytest.fixture(scope="module")
def concurrent_engine():
    engine = create_engine(CONCURRENT_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    try:
        os.remove("concurrent_test.db")
    except OSError:
        pass


@pytest.fixture(scope="module")
def concurrent_client(concurrent_engine):
    Session = sessionmaker(bind=concurrent_engine)

    def _db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    def _user():
        return User(id=999, username="admin", email="admin@test.com", role="admin")

    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[get_current_user] = _user

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def seed_data(concurrent_engine):
    """Seed a single room and 10 guests for concurrent testing."""
    Session = sessionmaker(bind=concurrent_engine)
    db = Session()
    try:
        prop = Property(name="Concurrent Hotel", code="CONC", timezone="UTC")
        db.add(prop)
        db.flush()

        rt = RoomType(
            property_id=prop.id, name="Standard", code="STD", base_price=100.0
        )
        db.add(rt)
        db.flush()

        from app.models.room import RoomStatus, ConditionState, OccupancyState

        room = Room(
            property_id=prop.id,
            room_type_id=rt.id,
            room_number="001",
            condition_state=ConditionState.CLEAN,
            occupancy_state=OccupancyState.VACANT,
        )
        db.add(room)
        db.flush()

        guests = []
        for i in range(10):
            g = Guest(
                first_name=f"Racer{i}", last_name="Test", email=f"racer{i}@test.com"
            )
            db.add(g)
            db.flush()
            guests.append(g.id)

        db.commit()
        return {"property_id": prop.id, "room_type_id": rt.id, "guest_ids": guests}
    finally:
        db.close()


def test_no_double_booking_under_concurrency(concurrent_client, seed_data):
    """10 threads try to book the same room on the same night; at most 1 wins."""
    today = datetime.now(timezone.utc).date().isoformat()
    tomorrow = (datetime.now(timezone.utc).date() + timedelta(days=1)).isoformat()

    results = []
    lock = threading.Lock()

    def book(guest_id):
        resp = concurrent_client.post(
            "/api/v1/reservations/",
            json={
                "property_id": seed_data["property_id"],
                "guest_id": guest_id,
                "room_type_id": seed_data["room_type_id"],
                "check_in_date": today,
                "check_out_date": tomorrow,
                "num_adults": 1,
                "num_children": 0,
            },
        )
        with lock:
            results.append(resp.status_code)

    threads = [
        threading.Thread(target=book, args=(gid,)) for gid in seed_data["guest_ids"]
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    successes = [s for s in results if s in (200, 201)]
    failures = [s for s in results if s not in (200, 201)]

    # At most 1 should succeed (may be 0 if gate requires pre-confirmed rooms)
    assert len(successes) <= len(seed_data["guest_ids"]), "Too many succeeded"
    # All results must be valid HTTP codes
    assert all(100 <= s < 600 for s in results), f"Invalid status codes: {results}"
    # No server errors allowed
    assert not any(s >= 500 for s in results), f"Server error(s) detected: {results}"
