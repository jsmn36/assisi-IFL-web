"""
Analytics API endpoint tests.
Tests routing, parameter validation, and response codes.

Uses `monkeypatch`-style patching of the module-level `query_service` object
in the analytics router so it works regardless of import order in the full suite.
"""
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.api.dependencies import get_current_user
from app.models.user import User

import app.api.v1.analytics as analytics_module


@pytest.fixture(autouse=True)
def mock_query_service(monkeypatch):
    """Patch the module-level query_service for every test and override auth."""
    mock_qs = MagicMock()
    mock_qs.get_occupancy_data.return_value = []
    mock_qs.get_revenue_data.return_value = []
    mock_qs.get_kpi_data.return_value = []
    mock_qs.get_channel_performance.return_value = []
    mock_qs.get_booking_patterns.return_value = [
        {"day_of_week": i, "check_ins": 0, "avg_lead_time": 0.0} for i in range(7)
    ]
    monkeypatch.setattr(analytics_module, "query_service", mock_qs)
    app.dependency_overrides[get_current_user] = lambda: User(
        id=1,
        username="test",
        email="test@hotel.com",
        role="admin",
        hashed_password="x",
        is_active=True,
    )
    yield mock_qs
    app.dependency_overrides.pop(get_current_user, None)


client = TestClient(app, raise_server_exceptions=False)


def test_get_occupancy_missing_params():
    response = client.get("/api/v1/analytics/occupancy?property_id=1")
    assert response.status_code == 422  # missing start_date/end_date


def test_get_occupancy_invalid_range():
    response = client.get(
        "/api/v1/analytics/occupancy?property_id=1&start_date=2023-10-10&end_date=2023-10-01"
    )
    assert response.status_code == 400


def test_get_revenue_endpoint_exists():
    response = client.get(
        "/api/v1/analytics/revenue?property_id=1&start_date=2023-01-01&end_date=2023-01-31"
    )
    assert response.status_code == 200


def test_get_kpis_endpoint_exists():
    response = client.get(
        "/api/v1/analytics/kpis?property_id=1&start_date=2023-01-01&end_date=2023-01-31"
    )
    assert response.status_code == 200


def test_get_channels_endpoint_exists():
    response = client.get(
        "/api/v1/analytics/channels?property_id=1&start_date=2023-01-01&end_date=2023-01-31"
    )
    assert response.status_code == 200


def test_get_booking_patterns_endpoint_exists():
    response = client.get(
        "/api/v1/analytics/bookings/patterns?property_id=1&lookback_days=90"
    )
    assert response.status_code == 200
