"""
Background Task Tests
Test Celery tasks
"""
import pytest
from app.config import settings

if not settings.is_postgresql_mode:
    pytest.skip("Celery tasks require PostgreSQL mode", allow_module_level=True)

from datetime import date, timedelta
from app.tasks.core import (
    test_task,
    process_reservation_confirmation,
    calculate_revenue_metrics,
)
from app.tasks.emails import send_confirmation_email
from app.tasks.reports import (
    generate_revenue_report_task,
    generate_occupancy_report_task,
)
from app.tasks.maintenance import (
    cleanup_old_audit_logs,
    update_room_status,
    calculate_daily_statistics,
)


def test_test_task():
    """Test basic task execution"""
    message = "Hello from test"
    result = test_task(message)

    assert result is not None
    assert result["message"] == message
    assert "timestamp" in result


@pytest.mark.skip(reason="Payment model not yet implemented")
def test_calculate_revenue_metrics():
    """Test revenue metrics calculation"""
    today = date.today()
    yesterday = today - timedelta(days=1)

    result = calculate_revenue_metrics(yesterday.isoformat(), today.isoformat())

    assert result is not None
    assert "total_revenue" in result
    assert "reservation_count" in result
    assert "average_daily_rate" in result


@pytest.mark.skip(reason="Payment model not yet implemented")
def test_generate_revenue_report_task(test_db):
    """Test revenue report generation"""
    today = date.today()
    yesterday = today - timedelta(days=1)

    result = generate_revenue_report_task(yesterday.isoformat(), today.isoformat())

    assert result is not None
    assert result["format"] == "json"
    assert "data" in result


def test_generate_occupancy_report_task(test_db):
    """Test occupancy report generation"""
    today = date.today()
    yesterday = today - timedelta(days=1)

    result = generate_occupancy_report_task(yesterday.isoformat(), today.isoformat())

    assert result is not None
    assert "total_rooms" in result
    assert "average_occupancy" in result


def test_cleanup_old_audit_logs(test_db):
    """Test audit log cleanup"""
    result = cleanup_old_audit_logs(days=90)

    assert result is not None
    assert "old_logs_count" in result
    assert result["days"] == 90


@pytest.mark.skip(
    reason="SQLite test DB does not support SQLEnum for Room.status column"
)
def test_update_room_status(test_db):
    """Test room status update"""
    result = update_room_status()

    assert result is not None
    assert "total_rooms" in result
    assert "updated" in result


def test_calculate_daily_statistics(test_db):
    """Test daily statistics calculation"""
    result = calculate_daily_statistics()

    assert result is not None
    assert "occupancy_rate" in result
    assert "revenue_today" in result
    assert "checkins_today" in result


def test_task_with_retry():
    """Test task retry mechanism"""
    pass


def test_task_caching():
    """Test cached task deduplication"""
    pass
