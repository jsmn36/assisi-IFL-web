"""
Test Search Service
"""
import pytest
from app.services.search_service import SearchService
from app.services.auth_service import AuthService
from app.services.reservation_service import ReservationService
from app.services.guest_service import GuestService
from app.services.room_service import RoomService
from app.models import User


def test_global_search(test_db):
    """Test global search"""
    auth_service = AuthService(test_db)
    search_service = SearchService(test_db)

    user = auth_service.create_user(
        username="testuser", email="test@example.com", password="password123"
    )

    room_service = RoomService(test_db)
    room = room_service.create_room(
        room_number="101", room_type="standard", floor=1, base_price=100.0
    )

    guest_service = GuestService(test_db)
    guest = guest_service.create_guest(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="1234567890",
    )

    results = search_service.global_search(query="john", user_id=user.id)

    assert results["total"] > 0
    assert "guests" in results["results"]


def test_search_reservations(test_db):
    """Test searching reservations"""
    search_service = SearchService(test_db)
    room_service = RoomService(test_db)
    guest_service = GuestService(test_db)
    reservation_service = ReservationService(test_db)

    room = room_service.create_room(
        room_number="101",
        room_type="standard",
        floor=1,
        max_occupancy=2,
        base_price=100.0,
    )

    guest = guest_service.create_guest(
        first_name="John", last_name="Doe", email="john@example.com", phone="1234567890"
    )

    from datetime import date, timedelta

    check_in = date.today() + timedelta(days=1)
    check_out = check_in + timedelta(days=2)

    reservation = reservation_service.create_reservation(
        guest_id=guest.id,
        room_type_id=room.room_type_id,
        property_id=1,
        check_in_date=check_in,
        check_out_date=check_out,
        num_adults=2,
    )

    results = search_service.search_reservations(
        query=reservation.confirmation_number[:4]
    )

    assert len(results) > 0
    assert results[0].confirmation_number == reservation.confirmation_number


def test_search_guests(test_db):
    """Test searching guests"""
    search_service = SearchService(test_db)
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

    results = search_service.search_guests(query="alice")
    assert len(results) == 1
    assert results[0].first_name == "Alice"

    results = search_service.search_guests(query="bob@example")
    assert len(results) == 1
    assert results[0].email == "bob@example.com"


def test_save_search(test_db):
    """Test saving search"""
    auth_service = AuthService(test_db)
    search_service = SearchService(test_db)

    user = auth_service.create_user(
        username="testuser", email="test@example.com", password="password123"
    )

    saved = search_service.save_search(
        user_id=user.id,
        name="My Search",
        entity_type="reservation",
        search_params={"query": "test", "status": "confirmed"},
        is_default=True,
    )

    assert saved.name == "My Search"
    assert saved.is_default is True
    assert saved.search_params["query"] == "test"


def test_get_saved_searches(test_db):
    """Test getting saved searches"""
    auth_service = AuthService(test_db)
    search_service = SearchService(test_db)

    user = auth_service.create_user(
        username="testuser", email="test@example.com", password="password123"
    )

    search_service.save_search(
        user_id=user.id, name="Search 1", entity_type="reservation", search_params={}
    )

    search_service.save_search(
        user_id=user.id, name="Search 2", entity_type="guest", search_params={}
    )

    searches = search_service.get_saved_searches(user_id=user.id)
    assert len(searches) == 2

    searches = search_service.get_saved_searches(
        user_id=user.id, entity_type="reservation"
    )
    assert len(searches) == 1


def test_use_saved_search(test_db):
    """Test using saved search"""
    auth_service = AuthService(test_db)
    search_service = SearchService(test_db)

    user = auth_service.create_user(
        username="testuser", email="test@example.com", password="password123"
    )

    saved = search_service.save_search(
        user_id=user.id, name="My Search", entity_type="reservation", search_params={}
    )

    used = search_service.use_saved_search(saved.id, user.id)

    assert used is not None
    assert used.use_count == 1
    assert used.last_used is not None


def test_delete_saved_search(test_db):
    """Test deleting saved search"""
    auth_service = AuthService(test_db)
    search_service = SearchService(test_db)

    user = auth_service.create_user(
        username="testuser", email="test@example.com", password="password123"
    )

    saved = search_service.save_search(
        user_id=user.id, name="My Search", entity_type="reservation", search_params={}
    )

    deleted = search_service.delete_saved_search(saved.id, user.id)
    assert deleted is True

    searches = search_service.get_saved_searches(user_id=user.id)
    assert len(searches) == 0


def test_track_search(test_db):
    """Test tracking search"""
    auth_service = AuthService(test_db)
    search_service = SearchService(test_db)

    user = auth_service.create_user(
        username="testuser", email="test@example.com", password="password123"
    )

    history = search_service.track_search(
        user_id=user.id,
        entity_type="reservation",
        search_term="test query",
        result_count=5,
    )

    assert history.search_term == "test query"
    assert history.result_count == 5


def test_get_search_history(test_db):
    """Test getting search history"""
    auth_service = AuthService(test_db)
    search_service = SearchService(test_db)

    user = auth_service.create_user(
        username="testuser", email="test@example.com", password="password123"
    )

    search_service.track_search(
        user_id=user.id, entity_type="reservation", search_term="query 1"
    )

    search_service.track_search(
        user_id=user.id, entity_type="guest", search_term="query 2"
    )

    history = search_service.get_search_history(user_id=user.id)
    assert len(history) == 2


def test_get_search_suggestions(test_db):
    """Test getting search suggestions"""
    auth_service = AuthService(test_db)
    search_service = SearchService(test_db)

    user = auth_service.create_user(
        username="testuser", email="test@example.com", password="password123"
    )

    search_service.track_search(
        user_id=user.id, entity_type="reservation", search_term="john smith"
    )

    search_service.track_search(
        user_id=user.id, entity_type="reservation", search_term="john doe"
    )

    suggestions = search_service.get_search_suggestions(
        user_id=user.id, entity_type="reservation", partial_query="joh"
    )

    assert len(suggestions) == 2


def test_create_quick_filter(test_db):
    """Test creating quick filter"""
    search_service = SearchService(test_db)

    filter = search_service.create_quick_filter(
        name="Today's Check-ins",
        entity_type="reservation",
        filter_config={"status": "confirmed"},
        icon="calendar",
        color="blue",
        created_by="admin",
    )

    assert filter.name == "Today's Check-ins"
    assert filter.icon == "calendar"


def test_get_quick_filters(test_db):
    """Test getting quick filters"""
    search_service = SearchService(test_db)

    search_service.create_quick_filter(
        name="Filter 1", entity_type="reservation", filter_config={}
    )

    search_service.create_quick_filter(
        name="Filter 2", entity_type="guest", filter_config={}
    )

    filters = search_service.get_quick_filters()
    assert len(filters) == 2

    filters = search_service.get_quick_filters(entity_type="reservation")
    assert len(filters) == 1
