"""
Task Integration Tests
Test task API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.mark.skip(reason="Task API endpoints not yet implemented")
def test_generate_revenue_report_api(admin_token):
    """Test revenue report API"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.post(
        "/api/v1/tasks/reports/revenue",
        params={
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "export_format": "json",
        },
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "queued"


@pytest.mark.skip(reason="Task API endpoints not yet implemented")
def test_get_task_status_api(admin_token):
    """Test task status API"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.post(
        "/api/v1/tasks/reports/revenue",
        params={"start_date": "2024-01-01", "end_date": "2024-01-31"},
        headers=headers,
    )

    task_id = response.json()["task_id"]

    response = client.get(f"/api/v1/tasks/status/{task_id}", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task_id


@pytest.mark.skip(reason="Task API endpoints not yet implemented")
def test_get_active_tasks_api(admin_token):
    """Test active tasks API"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.get("/api/v1/tasks/active", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "active" in data


def test_task_monitoring_history_api(admin_token):
    """Test task monitoring history API"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.get("/api/v1/task-monitoring/history", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "tasks" in data


def test_task_monitoring_statistics_api(admin_token):
    """Test task statistics API"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.get("/api/v1/task-monitoring/statistics", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "total_tasks" in data
    assert "by_status" in data


@pytest.mark.skip(reason="Task cancel endpoint not yet implemented")
def test_unauthorized_task_access(test_user_token):
    """Test that non-admin cannot access admin-only endpoints"""
    headers = {"Authorization": f"Bearer {test_user_token}"}

    response = client.post("/api/v1/tasks/cancel/fake-task-id", headers=headers)

    assert response.status_code == 403
