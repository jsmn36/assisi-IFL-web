"""
ETL Orchestrator tests.
Tests the run_etl_cycle method with mocked extractor, transformer, and loader.
"""
import pandas as pd
from unittest.mock import Mock, patch, MagicMock


@patch("app.services.analytics.etl.DataLoader")
@patch("app.services.analytics.etl.DataTransformer")
@patch("app.services.analytics.etl.DataExtractor")
def test_etl_orchestrator(MockExtractor, MockTransformer, MockLoader):
    from app.services.analytics.etl import ETLOrchestrator

    orchestrator = ETLOrchestrator()

    # Override with controllable mocks
    mock_extractor = orchestrator.extractor
    mock_transformer = orchestrator.transformer
    mock_loader = orchestrator.loader

    # Mock extract_all to return non-empty DataFrames
    mock_extractor.extract_all.return_value = {
        "reservations": pd.DataFrame([{"id": 1}]),
        "stays": pd.DataFrame([{"id": 1}]),
        "charges": pd.DataFrame([{"id": 1}]),
    }
    mock_extractor.get_properties.return_value = pd.DataFrame(
        [{"property_id": 1, "property_name": "Test Hotel", "total_rooms": 100}]
    )
    mock_extractor.get_room_types.return_value = pd.DataFrame(
        [{"room_type_id": 1, "room_type_name": "Standard"}]
    )
    mock_extractor.get_guests.return_value = pd.DataFrame(
        [{"guest_id": 1, "guest_country": "US", "guest_loyalty_tier": "Gold"}]
    )
    mock_extractor.get_rooms.return_value = pd.DataFrame(
        [{"room_id": 1, "room_number": "101"}]
    )

    # Mock transform returns
    mock_transformer.transform_reservations.return_value = pd.DataFrame(
        [{"reservation_id": 1, "property_id": 1}]
    )
    mock_transformer.transform_stays.return_value = pd.DataFrame(
        [{"stay_id": 1, "property_id": 1}]
    )
    mock_transformer.transform_charges.return_value = pd.DataFrame([{"charge_id": 1}])
    mock_transformer.calculate_daily_metrics.return_value = {
        "metric_date": "2023-01-10",
        "property_id": 1,
        "rooms_occupied": 50,
        "occupancy_percent": 50.0,
    }

    # Mock loader returns
    mock_loader.upsert_fact_reservations.return_value = 1
    mock_loader.upsert_fact_stays.return_value = 1
    mock_loader.upsert_fact_charges.return_value = 1
    mock_loader.upsert_daily_metrics.return_value = 1

    # Run the orchestrator
    orchestrator.run_etl_cycle()

    # Verify calls
    assert mock_extractor.extract_all.called
    assert mock_transformer.transform_reservations.called
    assert mock_transformer.transform_stays.called
    assert mock_transformer.transform_charges.called
    assert mock_transformer.calculate_daily_metrics.called
    assert mock_loader.upsert_fact_reservations.called
    assert mock_loader.upsert_fact_stays.called
    assert mock_loader.upsert_fact_charges.called
    assert mock_loader.upsert_daily_metrics.called
    assert mock_loader.log_sync_completion.called
