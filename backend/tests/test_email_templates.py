"""
Email Template Tests
Test template rendering and email sending
"""
import pytest
from datetime import date, timedelta
from app.services.template_service import template_service
from app.services.enhanced_email_service import EnhancedEmailService, EmailTemplates


def test_template_service_initialization():
    """Test template service initializes"""
    assert template_service is not None
    assert template_service.template_dir.exists()


def test_list_templates():
    """Test listing available templates"""
    templates = template_service.list_templates()
    assert len(templates) > 0
    assert any("reservation_confirmation" in t for t in templates)


def test_render_confirmation_template():
    """Test rendering reservation confirmation template"""
    context = {
        "guest_name": "Test Guest",
        "confirmation_code": "TEST123",
        "check_in_date": date.today(),
        "check_out_date": date.today() + timedelta(days=3),
        "room_type": "Deluxe",
        "number_of_guests": 2,
        "total_amount": 300.00,
        "management_url": "https://test.com",
    }

    html = template_service.render_template("reservation_confirmation.html", context)

    assert "Test Guest" in html
    assert "TEST123" in html
    assert "Deluxe" in html


def test_render_text_template():
    """Test rendering plain text template"""
    context = {
        "guest_name": "Test Guest",
        "confirmation_code": "TEST123",
        "check_in_date": date.today(),
        "check_out_date": date.today() + timedelta(days=3),
        "room_type": "Deluxe",
        "number_of_guests": 2,
        "total_amount": 300.00,
        "management_url": "https://test.com",
    }

    text = template_service.render_text_template(
        "reservation_confirmation.txt", context
    )

    assert "Test Guest" in text
    assert "TEST123" in text


def test_currency_filter():
    """Test currency formatting filter"""
    formatted = template_service.format_currency(1234.56)
    assert formatted == "$1,234.56"


def test_date_filter():
    """Test date formatting filter"""
    test_date = date(2024, 1, 15)
    formatted = template_service.format_date(test_date)
    assert "January" in formatted
    assert "15" in formatted
    assert "2024" in formatted


def test_template_variables():
    """Test getting template variables"""
    variables = template_service.get_template_variables("reservation_confirmation.html")

    assert "guest_name" in variables
    assert "confirmation_code" in variables


def test_enhanced_email_service(test_db):
    """Test enhanced email service"""
    service = EnhancedEmailService(test_db)
    assert service is not None


def test_preview_template(test_db):
    """Test template preview"""
    service = EnhancedEmailService(test_db)

    context = {
        "guest_name": "Preview Guest",
        "confirmation_code": "PREV123",
        "check_in_date": date.today(),
        "check_out_date": date.today() + timedelta(days=2),
        "room_type": "Standard",
        "number_of_guests": 1,
        "total_amount": 200.00,
        "management_url": "https://test.com",
    }

    preview = service.preview_template("reservation_confirmation", context)

    assert "html" in preview
    assert "text" in preview
    assert "Preview Guest" in preview["html"]
