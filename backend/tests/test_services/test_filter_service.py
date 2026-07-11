"""
Test Filter Service
"""
import pytest
from app.services.filter_service import FilterService
from app.services.guest_service import GuestService
from app.models import Guest


def test_apply_filters(test_db):
    """Test applying filters"""
    filter_service = FilterService(test_db)
    guest_service = GuestService(test_db)

    guest1 = guest_service.create_guest(
        first_name="Alice",
        last_name="Smith",
        email="alice@example.com",
        phone="1111111111",
    )

    guest2 = guest_service.create_guest(
        first_name="Bob", last_name="Jones", email="bob@example.com", phone="2222222222"
    )

    query = test_db.query(Guest)

    filters = [{"field": "first_name", "operator": "equals", "value": "Alice"}]

    filtered_query = filter_service.apply_filters(query, Guest, filters)
    results = filtered_query.all()

    assert len(results) == 1
    assert results[0].first_name == "Alice"


def test_filter_operators(test_db):
    """Test filter operators"""
    filter_service = FilterService(test_db)
    guest_service = GuestService(test_db)

    guest1 = guest_service.create_guest(
        first_name="Alice",
        last_name="Smith",
        email="alice@example.com",
        phone="1111111111",
    )

    guest2 = guest_service.create_guest(
        first_name="Bob", last_name="Jones", email="bob@example.com", phone="2222222222"
    )

    query = test_db.query(Guest)
    filters = [{"field": "email", "operator": "contains", "value": "alice"}]
    results = filter_service.apply_filters(query, Guest, filters).all()
    assert len(results) == 1

    query = test_db.query(Guest)
    filters = [{"field": "first_name", "operator": "not_equals", "value": "Alice"}]
    results = filter_service.apply_filters(query, Guest, filters).all()
    assert all(g.first_name != "Alice" for g in results)


def test_get_filter_operators(test_db):
    """Test getting filter operators"""
    filter_service = FilterService(test_db)

    operators = filter_service.get_filter_operators()

    assert len(operators) > 0
    assert any(op["value"] == "equals" for op in operators)
    assert any(op["value"] == "contains" for op in operators)


def test_validate_filter(test_db):
    """Test filter validation"""
    filter_service = FilterService(test_db)

    result = filter_service.validate_filter(
        Guest, {"field": "first_name", "operator": "equals", "value": "Alice"}
    )
    assert result["valid"] is True

    result = filter_service.validate_filter(
        Guest, {"field": "invalid_field", "operator": "equals", "value": "test"}
    )
    assert result["valid"] is False

    result = filter_service.validate_filter(
        Guest, {"field": "first_name", "value": "Alice"}
    )
    assert result["valid"] is False


def test_get_filterable_fields(test_db):
    """Test getting filterable fields"""
    filter_service = FilterService(test_db)

    fields = filter_service.get_filterable_fields("reservation")
    assert len(fields) > 0
    assert any(f["name"] == "confirmation_code" for f in fields)
    assert any(f["name"] == "status" for f in fields)

    fields = filter_service.get_filterable_fields("guest")
    assert len(fields) > 0
    assert any(f["name"] == "first_name" for f in fields)
    assert any(f["name"] == "email" for f in fields)
