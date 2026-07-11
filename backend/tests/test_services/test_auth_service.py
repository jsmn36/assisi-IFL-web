"""
Test Authentication Service
"""
import pytest
from app.services.auth_service import AuthService
from app.models import User, AuditLog
from app.core.security import verify_password


def test_create_user(test_db):
    """Test creating user"""
    service = AuthService(test_db)
    user = service.create_user(
        username="testuser",
        email="test@example.com",
        password="password123",
        role="staff",
        created_by="admin",
    )
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.role == "staff"
    assert verify_password("password123", user.hashed_password)


def test_create_duplicate_user(test_db):
    """Test creating duplicate user fails"""
    service = AuthService(test_db)
    service.create_user(
        username="testuser", email="test@example.com", password="password123"
    )
    with pytest.raises(ValueError, match="Username or email already exists"):
        service.create_user(
            username="testuser", email="different@example.com", password="password123"
        )


def test_authenticate_user_success(test_db):
    """Test successful authentication"""
    service = AuthService(test_db)
    service.create_user(
        username="testuser", email="test@example.com", password="password123"
    )
    user, access_token, refresh_token, _ = service.authenticate_user(
        username="testuser", password="password123"
    )
    assert user is not None
    assert user.username == "testuser"
    assert access_token is not None
    assert refresh_token is not None


def test_authenticate_user_wrong_password(test_db):
    """Test authentication with wrong password"""
    service = AuthService(test_db)
    service.create_user(
        username="testuser", email="test@example.com", password="password123"
    )
    user, access_token, refresh_token, _ = service.authenticate_user(
        username="testuser", password="wrongpassword"
    )
    assert user is None
    assert access_token is None
    assert refresh_token is None


def test_authenticate_user_not_found(test_db):
    """Test authentication with non-existent user"""
    service = AuthService(test_db)
    user, access_token, refresh_token, _ = service.authenticate_user(
        username="nonexistent", password="password123"
    )
    assert user is None
    assert access_token is None
    assert refresh_token is None


def test_account_lockout(test_db):
    """Test account lockout after failed attempts"""
    service = AuthService(test_db)
    service.create_user(
        username="testuser", email="test@example.com", password="password123"
    )
    for i in range(5):
        service.authenticate_user(username="testuser", password="wrongpassword")
    user = test_db.query(User).filter(User.username == "testuser").first()
    assert user.failed_login_attempts == 5
    assert user.is_locked()
    user, access_token, refresh_token, _ = service.authenticate_user(
        username="testuser", password="password123"
    )
    assert user is None


def test_change_password(test_db):
    """Test password change"""
    service = AuthService(test_db)
    user = service.create_user(
        username="testuser", email="test@example.com", password="password123"
    )
    success = service.change_password(
        user_id=user.id, old_password="password123", new_password="newpassword456"
    )
    assert success is True
    user, access_token, refresh_token, _ = service.authenticate_user(
        username="testuser", password="newpassword456"
    )
    assert user is not None


def test_change_password_wrong_old_password(test_db):
    """Test password change with wrong old password"""
    service = AuthService(test_db)
    user = service.create_user(
        username="testuser", email="test@example.com", password="password123"
    )
    success = service.change_password(
        user_id=user.id, old_password="wrongpassword", new_password="newpassword456"
    )
    assert success is False


def test_refresh_token(test_db):
    """Test refresh token"""
    service = AuthService(test_db)
    service.create_user(
        username="testuser", email="test@example.com", password="password123"
    )
    user, access_token, refresh_token, _ = service.authenticate_user(
        username="testuser", password="password123"
    )
    new_access_token = service.refresh_access_token(refresh_token)
    assert new_access_token is not None


def test_logout(test_db):
    """Test logout"""
    service = AuthService(test_db)
    user = service.create_user(
        username="testuser", email="test@example.com", password="password123"
    )
    _, _, refresh_token, _ = service.authenticate_user(
        username="testuser", password="password123"
    )
    service.logout(user.id, refresh_token)
    new_access_token = service.refresh_access_token(refresh_token)
    assert new_access_token is None


def test_audit_logging(test_db):
    """Test audit logging"""
    service = AuthService(test_db)
    service.create_user(
        username="testuser", email="test@example.com", password="password123"
    )
    service.authenticate_user(
        username="testuser", password="password123", ip_address="192.168.1.1"
    )
    logs = (
        test_db.query(AuditLog)
        .filter(AuditLog.username == "testuser", AuditLog.action == "login")
        .all()
    )
    assert len(logs) > 0
    assert logs[0].status == "success"
    assert logs[0].ip_address == "192.168.1.1"


def test_user_permissions(test_db):
    """Test user permissions"""
    service = AuthService(test_db)
    admin = service.create_user(
        username="admin",
        email="admin@example.com",
        password="password123",
        role="admin",
    )
    staff = service.create_user(
        username="staff",
        email="staff@example.com",
        password="password123",
        role="staff",
    )
    assert admin.has_permission("create_reservation")
    assert admin.has_permission("modify_settings")
    assert staff.has_permission("view_dashboard")
    assert not staff.has_permission("modify_settings")


def test_user_roles(test_db):
    """Test user roles"""
    service = AuthService(test_db)
    admin = service.create_user(
        username="admin",
        email="admin@example.com",
        password="password123",
        role="admin",
    )
    manager = service.create_user(
        username="manager",
        email="manager@example.com",
        password="password123",
        role="manager",
    )
    assert admin.has_role("admin")
    assert not admin.has_role("manager")
    assert manager.has_role("manager")
    assert not manager.has_role("admin")
    assert manager.has_role("manager", "admin")
