"""
Email Template Integration Tests
Test template API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_templates_api(admin_token):
    """Test list templates endpoint"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.get("/api/v1/email-templates/list", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "categories" in data
    assert "total" in data


def test_get_template_variables_api(admin_token):
    """Test get template variables endpoint"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.get(
        "/api/v1/email-templates/variables/reservation_confirmation", headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "variables" in data


def test_preview_template_api(admin_token):
    """Test preview template endpoint"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    from datetime import date, timedelta

    response = client.post(
        "/api/v1/email-templates/preview",
        headers=headers,
        json={
            "template_name": "reservation_confirmation",
            "context": {
                "guest_name": "API Test",
                "confirmation_code": "API123",
                "check_in_date": (date.today() + timedelta(days=1)).isoformat(),
                "check_out_date": (date.today() + timedelta(days=3)).isoformat(),
                "room_type": "Suite",
                "number_of_guests": 2,
                "total_amount": 500.00,
                "management_url": "https://test.com",
            },
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "html" in data
    assert "API Test" in data["html"]


def test_get_sample_data_api(admin_token):
    """Test get sample data endpoint"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.get(
        "/api/v1/email-templates/sample-data/reservation_confirmation", headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "guest_name" in data


@pytest.mark.skip(reason="notification-preferences route not yet implemented")
def test_notification_preferences_api(test_user_token):
    """Test notification preferences endpoints"""
    headers = {"Authorization": f"Bearer {test_user_token}"}

    # Get preferences
    response = client.get("/api/v1/notification-preferences", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "reservation" in data
    assert "payment" in data

    # Update preferences
    response = client.put(
        "/api/v1/notification-preferences",
        headers=headers,
        json={"promotional_emails": False, "newsletter": False},
    )

    assert response.status_code == 200


def test_unauthorized_template_access():
    """Test that unauthorized users cannot access templates"""
    response = client.get("/api/v1/email-templates/list")
    assert response.status_code in (401, 403)
