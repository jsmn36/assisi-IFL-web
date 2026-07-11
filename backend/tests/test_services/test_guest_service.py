import pytest
from app.services.guest_service import GuestService
from app.services.base_service import ValidationError, NotFoundError
from app.models import GuestType


def test_create_guest(test_db):
    service = GuestService(test_db)
    guest = service.create_guest(
        first_name="Charlie", last_name="Test", email="charlie@example.com"
    )
    assert guest.id is not None
    assert guest.full_name == "Charlie Test"


def test_create_duplicate_email_fails(test_db):
    service = GuestService(test_db)
    service.create_guest(first_name="First", last_name="Guest", email="dup@test.com")
    with pytest.raises(ValidationError):
        service.create_guest(
            first_name="Second", last_name="Guest", email="dup@test.com"
        )


def test_get_guest(test_db):
    service = GuestService(test_db)
    guest = service.create_guest(
        first_name="John", last_name="Doe", email="john@doe.com"
    )

    # Test get by ID
    assert service.get_guest(guest_id=guest.id).email == "john@doe.com"
    # Test get by email
    assert service.get_guest(email="john@doe.com").id == guest.id
    # Test not found
    with pytest.raises(NotFoundError):
        service.get_guest(email="missing@test.com")
    with pytest.raises(ValidationError):
        service.get_guest()


def test_update_guest(test_db):
    service = GuestService(test_db)
    guest = service.create_guest(
        first_name="Update", last_name="Me", email="up@test.com"
    )
    updated = service.update_guest(guest.id, first_name="Updated", is_vip=True)
    assert updated.first_name == "Updated"
    assert updated.is_vip is True


def test_search_guests(test_db):
    service = GuestService(test_db)
    service.create_guest(first_name="David", last_name="Search", email="david@test.com")
    results = service.search_guests(query="David")
    assert len(results) >= 1

    # Test filtered search
    results = service.search_guests(is_vip=True)
    assert len(results) == 0


def test_blacklist_workflow(test_db):
    service = GuestService(test_db)
    guest = service.create_guest(
        first_name="Bad", last_name="Guest", email="bad@test.com"
    )

    # Blacklist
    service.blacklist_guest(guest.id, "Reason")
    assert guest.is_blacklisted is True

    # Remove from blacklist
    service.remove_from_blacklist(guest.id)
    assert guest.is_blacklisted is False


def test_get_guest_reservations_empty(test_db):
    service = GuestService(test_db)
    guest = service.create_guest(first_name="G", last_name="R", email="gr@test.com")
    res = service.get_guest_reservations(guest.id)
    assert len(res) == 0
