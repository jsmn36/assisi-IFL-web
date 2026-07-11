"""
Test Analytics Services
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from app.services import KPIService
from app.services.analytics_service import AnalyticsService
from app.services.performance_service import PerformanceService
from app.models import (
    Property,
    RoomType,
    Room,
    RoomStatus,
    Guest,
    User,
    Reservation,
    ReservationStatus,
    Stay,
    StayStatus,
    Charge,
    ChargeType,
    DailyMetrics,
)


@pytest.fixture
def setup_analytics_test_data(test_db):
    """Setup test data for analytics tests"""
    property = Property(
        name="Analytics Hotel",
        code="AN",
        address_line1="123",
        city="C",
        state="S",
        postal_code="12345",
    )
    test_db.add(property)
    test_db.commit()

    room_type = RoomType(
        property_id=property.id,
        code="STD",
        name="Standard",
        base_price=Decimal("100"),
        max_occupancy=2,
        max_adults=2,
        max_children=1,
    )
    test_db.add(room_type)
    test_db.commit()

    rooms = []
    for i in range(1, 11):
        room = Room(
            property_id=property.id,
            room_type_id=room_type.id,
            room_number=f"10{i}",
            status=RoomStatus.AVAILABLE,
        )
        rooms.append(room)
    test_db.add_all(rooms)
    test_db.commit()

    guest = Guest(first_name="Test", last_name="Guest", email="test@analytics.com")
    test_db.add(guest)
    test_db.commit()

    today = date.today()

    for i in range(5):
        reservation = Reservation(
            property_id=property.id,
            guest_id=guest.id,
            room_type_id=room_type.id,
            confirmation_number=f"AN-{i:03d}",
            check_in_date=today - timedelta(days=1),
            check_out_date=today + timedelta(days=2),
            number_of_nights=3,
            num_adults=2,
            nightly_rate=Decimal("100"),
            total_amount=Decimal("300"),
            status=ReservationStatus.CHECKED_IN,
        )
        test_db.add(reservation)
        test_db.commit()

        stay = Stay(
            property_id=property.id,
            reservation_id=reservation.id,
            guest_id=guest.id,
            room_id=rooms[i].id,
            check_in_date=reservation.check_in_date,
            check_out_date=reservation.check_out_date,
            num_adults=2,
            nightly_rate=Decimal("100"),
            status=StayStatus.CHECKED_IN,
        )
        test_db.add(stay)
        test_db.commit()

        charge = Charge(
            property_id=property.id,
            stay_id=stay.id,
            guest_id=guest.id,
            charge_type=ChargeType.ROOM,
            description="Room charge",
            quantity=1,
            unit_price=10000,
            total_amount=10000,
            charge_date=today,
        )
        test_db.add(charge)

    test_db.commit()

    return property, room_type, rooms, guest


def test_calculate_daily_metrics(test_db, setup_analytics_test_data):
    """Test calculating daily metrics"""
    property, room_type, rooms, guest = setup_analytics_test_data

    service = KPIService(test_db)
    metrics = service.calculate_daily_metrics(property.id, date.today())

    assert metrics.total_rooms == 10
    assert metrics.occupied_rooms == 5
    assert metrics.available_rooms == 5
    assert float(metrics.occupancy_rate) == 50.0
    assert metrics.room_revenue == 50000


def test_get_daily_metrics_range(test_db, setup_analytics_test_data):
    """Test getting daily metrics for date range"""
    property, room_type, rooms, guest = setup_analytics_test_data

    service = KPIService(test_db)

    today = date.today()
    for i in range(3):
        service.calculate_daily_metrics(property.id, today - timedelta(days=i))

    metrics_list = service.get_daily_metrics(
        property.id, today - timedelta(days=2), today
    )

    assert len(metrics_list) == 3


def test_calculate_monthly_metrics(test_db, setup_analytics_test_data):
    """Test calculating monthly metrics"""
    property, room_type, rooms, guest = setup_analytics_test_data

    service = KPIService(test_db)

    today = date.today()
    for i in range(10):
        service.calculate_daily_metrics(property.id, today - timedelta(days=i))

    monthly = service.calculate_monthly_metrics(property.id, today.year, today.month)

    assert monthly is not None
    assert monthly.year == today.year
    assert monthly.month == today.month
    assert float(monthly.avg_occupancy_rate) > 0


def test_get_kpi_summary(test_db, setup_analytics_test_data):
    """Test getting KPI summary"""
    property, room_type, rooms, guest = setup_analytics_test_data

    service = KPIService(test_db)
    summary = service.get_kpi_summary(property.id, date.today())

    assert "occupancy" in summary
    assert "revenue" in summary
    assert "adr" in summary
    assert "revpar" in summary
    assert summary["occupancy"]["rate"] == 50.0


def test_occupancy_trends(test_db, setup_analytics_test_data):
    """Test occupancy trends"""
    property, room_type, rooms, guest = setup_analytics_test_data

    kpi_service = KPIService(test_db)
    analytics_service = AnalyticsService(test_db)

    today = date.today()
    for i in range(7):
        kpi_service.calculate_daily_metrics(property.id, today - timedelta(days=i))

    trends = analytics_service.get_occupancy_trends(
        property.id, today - timedelta(days=6), today, "daily"
    )

    assert "trend_data" in trends
    assert "statistics" in trends
    assert len(trends["trend_data"]) == 7
    assert trends["statistics"]["avg_occupancy"] > 0


def test_revenue_trends(test_db, setup_analytics_test_data):
    """Test revenue trends"""
    property, room_type, rooms, guest = setup_analytics_test_data

    kpi_service = KPIService(test_db)
    analytics_service = AnalyticsService(test_db)

    today = date.today()
    for i in range(7):
        kpi_service.calculate_daily_metrics(property.id, today - timedelta(days=i))

    trends = analytics_service.get_revenue_trends(
        property.id, today - timedelta(days=6), today, breakdown=True
    )

    assert "trend_data" in trends
    assert "totals" in trends
    assert len(trends["trend_data"]) == 7
    assert trends["totals"]["total_revenue"] > 0


def test_comparative_analysis(test_db, setup_analytics_test_data):
    """Test comparative analysis"""
    property, room_type, rooms, guest = setup_analytics_test_data

    kpi_service = KPIService(test_db)
    analytics_service = AnalyticsService(test_db)

    today = date.today()
    for i in range(14):
        kpi_service.calculate_daily_metrics(property.id, today - timedelta(days=i))

    comparison = analytics_service.get_comparative_analysis(
        property.id,
        today - timedelta(days=13),
        today - timedelta(days=7),
        today - timedelta(days=6),
        today,
    )

    assert "period1" in comparison
    assert "period2" in comparison
    assert "changes" in comparison
    assert "occupancy_change" in comparison["changes"]


def test_performance_scorecard(test_db, setup_analytics_test_data):
    """Test performance scorecard"""
    property, room_type, rooms, guest = setup_analytics_test_data

    kpi_service = KPIService(test_db)
    performance_service = PerformanceService(test_db)

    kpi_service.calculate_daily_metrics(property.id, date.today())

    scorecard = performance_service.get_performance_scorecard(property.id, date.today())

    assert "overall_score" in scorecard
    assert "scores" in scorecard
    assert "occupancy" in scorecard["scores"]
    assert scorecard["overall_score"] >= 0
    assert scorecard["overall_score"] <= 100


def test_efficiency_metrics(test_db, setup_analytics_test_data):
    """Test efficiency metrics"""
    property, room_type, rooms, guest = setup_analytics_test_data

    kpi_service = KPIService(test_db)
    performance_service = PerformanceService(test_db)

    today = date.today()
    for i in range(7):
        kpi_service.calculate_daily_metrics(property.id, today - timedelta(days=i))

    efficiency = performance_service.get_efficiency_metrics(
        property.id, today - timedelta(days=6), today
    )

    assert "occupancy" in efficiency
    assert "revenue_mix" in efficiency
    assert "conversion" in efficiency
    assert efficiency["occupancy"]["avg_occupancy_rate"] > 0


def test_forecast(test_db, setup_analytics_test_data):
    """Test revenue forecast"""
    property, room_type, rooms, guest = setup_analytics_test_data

    kpi_service = KPIService(test_db)
    performance_service = PerformanceService(test_db)

    today = date.today()
    for i in range(30):
        kpi_service.calculate_daily_metrics(property.id, today - timedelta(days=i))

    forecast = performance_service.get_forecast(property.id, 7)

    assert "forecast" in forecast
    assert len(forecast["forecast"]) == 7
    assert all("forecasted_revenue" in f for f in forecast["forecast"])
