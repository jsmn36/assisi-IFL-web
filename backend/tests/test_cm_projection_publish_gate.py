import pytest
import uuid
import json
from datetime import datetime, date, timedelta
from app.cm.gates.projection_publish import ProjectionPublishGate
from app.cm.models import AvailabilityCache, PricingCache
from app.cm.database import get_cm_db


@pytest.fixture
def mock_cm_db(mocker):
    mock_db = mocker.MagicMock()
    mock_session = mocker.MagicMock()
    mock_session.__enter__.return_value = mock_db
    mocker.patch("app.cm.gates.projection_publish.get_cm_db", return_value=mock_session)
    return mock_db


def test_projection_publish_invalid_type(mock_cm_db):
    gate = ProjectionPublishGate(uuid.uuid4(), 5, date(2026, 3, 20), "invalid_type")
    result = gate.execute()

    assert result.success is False
    assert result.error_code == "INVALID_PROJECTION_TYPE"


def test_projection_publish_availability_success(mock_cm_db, requests_mock):
    prop_id = uuid.uuid4()
    test_date = date(2026, 3, 20)

    gate = ProjectionPublishGate(prop_id, 5, test_date, "availability")

    # Mock PM server endpoint
    pms_response = {
        "property_id": str(prop_id),
        "room_type_id": 5,
        "availability": [
            {
                "date": "2026-03-20",
                "available_rooms": 3,
                "total_rooms": 10,
                "occupied_rooms": 7,
            }
        ],
        "checksum": "mock_checksum",
        "generated_at": "2026-03-20T10:30:00Z",
    }
    requests_mock.get(
        f"http://localhost:8000/api/v1/availability/query", json=pms_response
    )

    # Mock DB insert (no existing cache)
    mock_cm_db.query().filter().first.return_value = None

    result = gate.execute()

    assert result.success is True
    assert result.data == pms_response
    mock_cm_db.add.assert_called_once()
    mock_cm_db.commit.assert_called_once()

    added_cache = mock_cm_db.add.call_args[0][0]
    assert isinstance(added_cache, AvailabilityCache)
    assert added_cache.available_rooms == 3
    assert added_cache.total_rooms == 10


def test_projection_publish_pricing_success(mock_cm_db, requests_mock):
    prop_id = uuid.uuid4()
    test_date = date(2026, 3, 20)

    gate = ProjectionPublishGate(prop_id, 5, test_date, "pricing")

    pms_response = {
        "property_id": str(prop_id),
        "room_type_id": 5,
        "rates": [
            {
                "date": "2026-03-20",
                "amount": 120.00,
                "currency": "USD",
                "rate_plan_id": 1,
                "rate_plan_name": "Standard Rate",
            }
        ],
        "version": "v123",
        "generated_at": "2026-03-20T10:00:00Z",
    }
    requests_mock.get(f"http://localhost:8000/api/v1/rates/query", json=pms_response)

    # Mock DB update (existing cache)
    existing_cache = PricingCache()
    mock_cm_db.query().filter().first.return_value = existing_cache

    result = gate.execute()

    assert result.success is True
    assert result.data == pms_response
    mock_cm_db.add.assert_not_called()  # Because it was an update
    mock_cm_db.commit.assert_called_once()

    assert existing_cache.amount == 120.00
    assert existing_cache.currency == "USD"
    assert existing_cache.pms_rate_version == "v123"


def test_projection_publish_pms_fetch_error(mock_cm_db, requests_mock):
    prop_id = uuid.uuid4()
    test_date = date(2026, 3, 20)

    gate = ProjectionPublishGate(prop_id, 5, test_date, "availability")

    requests_mock.get(
        f"http://localhost:8000/api/v1/availability/query",
        status_code=500,
        text="Internal Server Error",
    )

    result = gate.execute()

    assert result.success is False
    assert result.error_code == "PMS_FETCH_ERROR"
    mock_cm_db.commit.assert_not_called()
