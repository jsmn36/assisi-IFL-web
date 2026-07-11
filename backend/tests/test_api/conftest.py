import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 1. Import the app and the base
from app.main import app
from app.database import Base
from app.api.dependencies import get_db, get_current_user
from app.models.user import User

# 2. FORCE IMPORT of ALL models to populate Metadata registry
# This ensures SQLAlchemy knows which tables to create
from app.models.property import Property
from app.models.room_type import RoomType
from app.models.room import Room
from app.models.guest import Guest
from app.models.reservation import Reservation
from app.models.stay import Stay
from app.models.charge import Charge
from app.models.rate_plan import RatePlan
from app.models.business_day import BusinessDay
from app.models.gate_history import GateHistory
from app.models.gate_execution_history import GateExecutionHistory
from app.models.state_transition_history import StateTransitionHistory
from app.models.group_reservation import GroupReservation

# 3. Setup a single, shared Test Database engine
TEST_DB = "test_api_v2.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///./{TEST_DB}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def init_db():
    """Create all tables once for the entire test session."""
    # Ensure a fresh start
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

    # Create tables based on the imported models above
    Base.metadata.create_all(bind=engine)

    yield

    # Optional: cleanup after all tests are done
    # os.remove(TEST_DB)


def override_get_db():
    """Dependency override for the FastAPI app."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_db():
    """Fixture to provide a DB session to test setup code."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    """Fixture to provide the TestClient with the DB override applied."""
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: User(
        id=1, email="test@hotel.com", role="admin"
    )
    with TestClient(app) as c:
        yield c
    # Clear overrides after test
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test-token"}
