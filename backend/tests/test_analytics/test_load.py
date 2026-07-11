"""
DataLoader tests.
Tests load operations with mocked database connections.
Uses correct method names: upsert_daily_metrics, log_sync_completion.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd


@patch(
    "app.services.analytics.load.get_analytics_db_url",
    return_value="sqlite:///:memory:",
)
@patch("app.services.analytics.load.create_engine")
def test_data_loader_upsert_daily_metrics(mock_create_engine, mock_url):
    from app.services.analytics.load import DataLoader

    loader = DataLoader()

    # Mock engine with context manager
    loader.engine = MagicMock()
    loader.engine.dialect.name = "sqlite"
    mock_conn = MagicMock()
    loader.engine.begin.return_value.__enter__ = Mock(return_value=mock_conn)
    loader.engine.begin.return_value.__exit__ = Mock(return_value=False)
    mock_conn.execute.return_value.rowcount = 1

    metrics = {
        "property_id": 1,
        "metric_date": "2023-01-01",
        "total_rooms": 100,
        "rooms_available": 100,
        "rooms_occupied": 80,
        "occupancy_percent": 80.0,
        "room_revenue": 8000.0,
        "food_revenue": 500.0,
        "beverage_revenue": 0.0,
        "spa_revenue": 0.0,
        "other_revenue": 100.0,
        "total_revenue": 8600.0,
        "adr": 100.0,
        "revpar": 80.0,
        "reservations_created": 10,
        "reservations_cancelled": 2,
        "check_ins": 15,
        "check_outs": 10,
    }

    result = loader.upsert_daily_metrics(metrics)
    assert mock_conn.execute.called
    assert result == 1


@patch(
    "app.services.analytics.load.get_analytics_db_url",
    return_value="sqlite:///:memory:",
)
@patch("app.services.analytics.load.create_engine")
def test_data_loader_upsert_fact_reservations(mock_create_engine, mock_url):
    from app.services.analytics.load import DataLoader

    loader = DataLoader()
    loader.engine = MagicMock()
    loader.engine.dialect.name = "sqlite"
    mock_conn = MagicMock()
    loader.engine.begin.return_value.__enter__ = Mock(return_value=mock_conn)
    loader.engine.begin.return_value.__exit__ = Mock(return_value=False)
    mock_conn.execute.return_value.rowcount = 1

    df = pd.DataFrame(
        [
            {
                "reservation_id": 1,
                "property_id": 1,
                "guest_id": 5,
                "room_type_id": 10,
                "booking_date": "2023-01-01",
                "check_in_date": "2023-01-10",
                "check_out_date": "2023-01-12",
                "nights": 2,
                "lead_time_days": 9,
                "status": "confirmed",
                "channel": "direct",
                "room_revenue": 500.0,
                "total_revenue": 500.0,
                "guest_country": "US",
                "guest_loyalty_tier": "Gold",
                "guests_count": 1,
                "property_name": "Test Hotel",
                "room_type_name": "Standard",
                "created_at": "2023-01-01T10:00:00",
                "updated_at": "2023-01-01T10:00:00",
            }
        ]
    )

    result = loader.upsert_fact_reservations(df)
    assert mock_conn.execute.called


@patch(
    "app.services.analytics.load.get_analytics_db_url",
    return_value="sqlite:///:memory:",
)
@patch("app.services.analytics.load.create_engine")
def test_data_loader_log_sync_completion(mock_create_engine, mock_url):
    from app.services.analytics.load import DataLoader

    loader = DataLoader()
    loader.engine = MagicMock()
    mock_conn = MagicMock()
    loader.engine.begin.return_value.__enter__ = Mock(return_value=mock_conn)
    loader.engine.begin.return_value.__exit__ = Mock(return_value=False)

    loader.log_sync_completion(
        table_name="reservations",
        records_extracted=100,
        records_transformed=95,
        records_loaded=95,
        duration_seconds=2.5,
        status="success",
    )
    assert mock_conn.execute.called
