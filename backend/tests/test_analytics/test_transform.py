"""
DataTransformer tests.
Tests transformation of raw PMS data to analytics-ready formats.
"""
import pytest
import pandas as pd
from datetime import date
from app.services.analytics.transform import DataTransformer


@pytest.fixture
def transformer():
    return DataTransformer()


def test_transform_reservations_empty(transformer):
    assert transformer.transform_reservations(
        pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    ).empty


def test_transform_reservations_valid(transformer):
    reservations_df = pd.DataFrame(
        [
            {
                "reservation_id": 100,
                "property_id": 1,
                "room_type_id": 10,
                "guest_id": 5,
                "created_at": "2023-01-01T10:00:00",
                "start_date": "2023-01-10T14:00:00",
                "end_date": "2023-01-12T11:00:00",
                "nights": 2,
            }
        ]
    )

    properties_df = pd.DataFrame(
        [{"property_id": 1, "property_name": "Downtown Hotel"}]
    )
    room_types_df = pd.DataFrame(
        [{"room_type_id": 10, "room_type_name": "Standard Room"}]
    )
    guests_df = pd.DataFrame(
        [{"guest_id": 5, "guest_country": "US", "guest_loyalty_tier": "Gold"}]
    )

    result = transformer.transform_reservations(
        reservations_df, properties_df, room_types_df, guests_df
    )

    assert not result.empty
    assert result.iloc[0]["property_name"] == "Downtown Hotel"
    assert result.iloc[0]["guest_country"] == "US"
    assert result.iloc[0]["booking_date"] == date(2023, 1, 1)
    assert result.iloc[0]["check_in_date"] == date(2023, 1, 10)


def test_calculate_daily_metrics(transformer):
    target_date = pd.Timestamp("2023-01-10")
    property_id = 1
    total_rooms = 100

    # Stays: both should count as occupied on 2023-01-10
    # Stay 1: checked in Jan 9, checking out Jan 12 → occupies room on Jan 10
    #   Logic: check_in_date <= Jan 10 AND check_out_date > Jan 10 → True
    # Stay 2: checked in Jan 10, checking out Jan 15 → occupies room on Jan 10
    #   Logic: check_in_date <= Jan 10 AND check_out_date > Jan 10 → True
    stays_df = pd.DataFrame(
        [
            {
                "property_id": 1,
                "check_in_date": pd.Timestamp("2023-01-09"),
                "check_out_date": pd.Timestamp("2023-01-12"),
            },
            {
                "property_id": 1,
                "check_in_date": pd.Timestamp("2023-01-10"),
                "check_out_date": pd.Timestamp("2023-01-15"),
            },
        ]
    )

    reservations_df = pd.DataFrame(
        [
            {
                "property_id": 1,
                "booking_date": pd.Timestamp("2023-01-10"),
                "status": "confirmed",
                "updated_at": pd.Timestamp("2023-01-10"),
            }
        ]
    )

    charges_df = pd.DataFrame(
        [
            {
                "property_id": 1,
                "posted_date": pd.Timestamp("2023-01-10"),
                "charge_type": "room",
                "amount": 250.0,
            },
            {
                "property_id": 1,
                "posted_date": pd.Timestamp("2023-01-10"),
                "charge_type": "food",
                "amount": 50.0,
            },
        ]
    )

    metrics = transformer.calculate_daily_metrics(
        target_date, property_id, stays_df, reservations_df, charges_df, total_rooms
    )

    assert metrics["rooms_occupied"] == 2
    assert metrics["occupancy_percent"] == 2.0
    assert metrics["room_revenue"] == 250.0
    assert metrics["food_revenue"] == 50.0
    assert metrics["total_revenue"] == 300.0
    assert metrics["adr"] == 125.0  # 250 / 2
    assert metrics["revpar"] == 2.5  # 250 / 100
    assert metrics["reservations_created"] == 1
    assert metrics["check_ins"] == 1  # one stay checks in on Jan 10
