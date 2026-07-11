"""
DataExtractor tests.
Tests extraction of PMS data with mocked database connections.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd


def _make_pms_connect(sequence):
    """
    Returns a side_effect callable for pms_engine.connect().
    Each call returns a fresh context manager whose __enter__ yields a mock
    connection returning the next row-list from `sequence` (cycled).
    """
    calls = {"n": 0}

    def side_effect():
        idx = calls["n"] % len(sequence)
        calls["n"] += 1
        rows = sequence[idx]

        result = MagicMock()
        result.mappings.return_value.all.return_value = rows

        conn = MagicMock()
        conn.execute.return_value = result

        ctx = MagicMock()
        ctx.__enter__ = Mock(return_value=conn)
        ctx.__exit__ = Mock(return_value=False)
        return ctx

    return side_effect


@patch(
    "app.services.analytics.extract.get_analytics_db_url",
    return_value="sqlite:///:memory:",
)
@patch(
    "app.services.analytics.extract.get_pms_db_url", return_value="sqlite:///:memory:"
)
@patch("app.services.analytics.extract.create_engine")
def test_data_extractor(mock_create_engine, mock_pms_url, mock_analytics_url):
    from app.services.analytics.extract import DataExtractor

    extractor = DataExtractor()
    extractor.pms_engine = MagicMock()
    extractor.pms_engine.dialect.name = "sqlite"
    extractor.analytics_engine = MagicMock()

    # --- analytics engine: get_last_sync_timestamp ---
    analytics_conn = MagicMock()
    analytics_conn.execute.return_value.fetchone.return_value = (
        pd.Timestamp("2023-01-01"),
    )
    analytics_ctx = MagicMock()
    analytics_ctx.__enter__ = Mock(return_value=analytics_conn)
    analytics_ctx.__exit__ = Mock(return_value=False)
    extractor.analytics_engine.connect.return_value = analytics_ctx

    assert extractor.get_last_sync_timestamp("reservations") == pd.Timestamp(
        "2023-01-01"
    )

    # --- row stubs ---
    reservation_rows = [
        {
            "reservation_id": 1,
            "property_id": 1,
            "guest_id": 1,
            "room_type_id": 1,
            "start_date": "2023-01-10",
            "end_date": "2023-01-12",
            "status": "confirmed",
            "channel": "direct",
            "created_at": "2023-01-01",
            "updated_at": "2023-01-10",
            "nights": 2,
            "lead_time_days": 9,
        }
    ]
    stay_rows = [
        {
            "stay_id": 1,
            "reservation_id": 1,
            "room_id": 1,
            "check_in_time": "2023-01-10T14:00:00",
            "check_out_time": "2023-01-12T11:00:00",
            "status": "checked_out",
            "created_at": "2023-01-01",
            "updated_at": "2023-01-12",
        }
    ]
    charge_rows = [
        {
            "charge_id": 1,
            "stay_id": 1,
            "amount": 100.0,
            "charge_type": "room",
            "description": "Nightly rate",
            "posted_date": "2023-01-10",
            "created_at": "2023-01-10",
            "updated_at": "2023-01-10",
        }
    ]
    property_rows = [
        {"property_id": 1, "property_name": "Test Hotel", "total_rooms": 100}
    ]
    room_type_rows = [{"room_type_id": 1, "room_type_name": "Standard"}]
    guest_rows = [{"guest_id": 1, "guest_country": "US", "guest_loyalty_tier": "Gold"}]
    room_rows = [{"room_id": 1, "room_number": "101"}]

    # The PMS engine is called once per extractor method; wire them in order.
    sequence = [
        reservation_rows,  # extract_reservations
        stay_rows,  # extract_stays
        charge_rows,  # extract_charges
        property_rows,  # get_properties
        room_type_rows,  # get_room_types
        guest_rows,  # get_guests
        room_rows,  # get_rooms
        reservation_rows,  # extract_all -> extract_reservations
        stay_rows,  # extract_all -> extract_stays
        charge_rows,  # extract_all -> extract_charges
    ]
    extractor.pms_engine.connect.side_effect = _make_pms_connect(sequence)

    df = extractor.extract_reservations()
    assert not df.empty
    assert len(df) == 1

    df = extractor.extract_stays()
    assert not df.empty

    df = extractor.extract_charges()
    assert not df.empty
    assert "charge_type" in df.columns
    assert "description" in df.columns
    assert "posted_date" in df.columns

    df = extractor.get_properties()
    assert not df.empty

    df = extractor.get_room_types()
    assert not df.empty

    df = extractor.get_rooms()
    assert not df.empty

    all_data = extractor.extract_all()
    assert "reservations" in all_data
    assert "stays" in all_data
    assert "charges" in all_data
