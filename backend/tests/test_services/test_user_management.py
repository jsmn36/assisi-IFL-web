"""
Test User Management Service
"""
import pytest
from app.services.user_management_service import UserManagementService
from app.services.auth_service import AuthService
from app.models import User


def test_get_users(test_db):
    """Test getting users"""
    auth_service = AuthService(test_db)

    for i in range(5):
        auth_service.create_user(
            username=f"testuser{i}",
            email=f"test{i}@example.com",
            password="password123",
            role="staff",
        )

    service = UserManagementService(test_db)
    result = service.get_users(skip=0, limit=10)

    assert result["total"] == 5
    assert len(result["users"]) == 5


def test_get_users_with_filters(test_db):
    """Test getting users with filters"""
    auth_service = AuthService(test_db)

    auth_service.create_user(
        username="admin1",
        email="admin@example.com",
        password="password123",
        role="admin",
    )
    auth_service.create_user(
        username="staff1",
        email="staff@example.com",
        password="password123",
        role="staff",
    )

    service = UserManagementService(test_db)

    result = service.get_users(role="admin")
    assert result["total"] == 1
    assert result["users"][0].role == "admin"


def test_get_users_with_search(test_db):
    """Test searching users"""
    auth_service = AuthService(test_db)

    auth_service.create_user(
        username="john_doe",
        email="john@example.com",
        password="password123",
        first_name="John",
        last_name="Doe",
    )

    service = UserManagementService(test_db)

    result = service.get_users(search="john")
    assert result["total"] == 1

    result = service.get_users(search="example.com")
    assert result["total"] >= 1


def test_update_user(test_db):
    """Test updating user"""
    auth_service = AuthService(test_db)
    service = UserManagementService(test_db)

    user = auth_service.create_user(
        username="testuser", email="test@example.com", password="password123"
    )

    updated_user = service.update_user(
        user_id=user.id,
        updated_by="admin",
        first_name="Test",
        last_name="User",
        phone="1234567890",
    )

    assert updated_user.first_name == "Test"
    assert updated_user.last_name == "User"
    assert updated_user.phone == "1234567890"


def test_update_user_duplicate_username(test_db):
    """Test updating user with duplicate username"""
    auth_service = AuthService(test_db)
    service = UserManagementService(test_db)

    user1 = auth_service.create_user(
        username="user1", email="user1@example.com", password="password123"
    )
    user2 = auth_service.create_user(
        username="user2", email="user2@example.com", password="password123"
    )

    with pytest.raises(ValueError, match="Username already exists"):
        service.update_user(user_id=user2.id, updated_by="admin", username="user1")


def test_deactivate_user(test_db):
    """Test deactivating user"""
    auth_service = AuthService(test_db)
    service = UserManagementService(test_db)

    user = auth_service.create_user(
        username="testuser", email="test@example.com", password="password123"
    )

    assert user.is_active is True

    deactivated = service.deactivate_user(user.id, "admin")

    assert deactivated.is_active is False


def test_activate_user(test_db):
    """Test activating user"""
    auth_service = AuthService(test_db)
    service = UserManagementService(test_db)

    user = auth_service.create_user(
        username="testuser", email="test@example.com", password="password123"
    )
    service.deactivate_user(user.id, "admin")

    activated = service.activate_user(user.id, "admin")

    assert activated.is_active is True


def test_reset_password(test_db):
    """Test admin password reset"""
    auth_service = AuthService(test_db)
    service = UserManagementService(test_db)

    user = auth_service.create_user(
        username="testuser", email="test@example.com", password="password123"
    )

    reset_user = service.reset_password(
        user_id=user.id, new_password="newpassword456", reset_by="admin"
    )

    user_auth, _, _, _ = auth_service.authenticate_user(
        username="testuser", password="newpassword456"
    )

    assert user_auth is not None


def test_unlock_account(test_db):
    """Test unlocking account"""
    auth_service = AuthService(test_db)
    service = UserManagementService(test_db)

    user = auth_service.create_user(
        username="testuser", email="test@example.com", password="password123"
    )

    for i in range(5):
        auth_service.authenticate_user(username="testuser", password="wrongpassword")

    locked_user = test_db.query(User).filter(User.id == user.id).first()
    assert locked_user.is_locked()

    unlocked = service.unlock_account(user.id, "admin")

    assert unlocked.failed_login_attempts == 0
    assert unlocked.locked_until is None
    assert not unlocked.is_locked()


def test_get_user_stats(test_db):
    """Test getting user statistics"""
    auth_service = AuthService(test_db)
    service = UserManagementService(test_db)

    user = auth_service.create_user(
        username="testuser", email="test@example.com", password="password123"
    )

    for i in range(3):
        auth_service.authenticate_user(username="testuser", password="password123")

    stats = service.get_user_stats(user.id)

    assert stats["username"] == "testuser"
    assert stats["login_count"] >= 3
    assert stats["total_activities"] > 0


def test_get_role_stats(test_db):
    """Test getting role statistics"""
    auth_service = AuthService(test_db)
    service = UserManagementService(test_db)

    auth_service.create_user(
        username="admin1",
        email="admin1@example.com",
        password="password123",
        role="admin",
    )
    auth_service.create_user(
        username="admin2",
        email="admin2@example.com",
        password="password123",
        role="admin",
    )
    auth_service.create_user(
        username="staff1",
        email="staff1@example.com",
        password="password123",
        role="staff",
    )

    stats = service.get_role_stats()

    assert stats["total_by_role"]["admin"] == 2
    assert stats["total_by_role"]["staff"] == 1
    assert stats["total_users"] == 3
