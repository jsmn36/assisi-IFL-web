"""
User Model - Enhanced with security features
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base
from app.models.mixins import TenantScopedMixin


class User(Base):
    """User Model"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(200), unique=True, nullable=False, index=True)
    hashed_password = Column(String(200), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    role = Column(String(50), nullable=False, default="staff")
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_email_verified = Column(Boolean, default=True, server_default="1", nullable=False)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    last_login = Column(DateTime, nullable=True)
    last_password_change = Column(DateTime, nullable=True)
    password_reset_token = Column(String(200), nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, onupdate=lambda: datetime.now(timezone.utc))
    created_by = Column(String(100), nullable=True)

    # Relationships
    profile = relationship("InstitutionProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    posts = relationship("Post", back_populates="institution", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username}>"

    def is_locked(self):
        if self.locked_until is None:
            return False
        locked_until = self.locked_until
        if locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) < locked_until

    def has_role(self, *roles):
        return self.role in roles

    def has_permission(self, permission: str) -> bool:
        if self.is_superuser or self.role.upper() == "ADMIN":
            return True
        
        role = self.role.upper()
        role_permissions = {
            "MANAGER": ["*"],
            "RECEPTIONIST": [
                "view_dashboard", "view_reservations", "create_reservation",
                "modify_reservation", "cancel_reservation", "check_in",
                "check_out", "view_guests", "create_guest", "view_rooms",
                "view_housekeeping", "view_charges", "create_charge",
                "view_payments", "create_payment",
            ],
            "CHEF": [
                "view_dashboard", "view_pos", "view_kds", "view_inventory",
                "view_housekeeping",
            ],
            "WAITER": [
                "view_dashboard", "view_pos", "create_order", "view_room_service",
            ],
            "INVENTORY STAFF": [
                "view_dashboard", "view_inventory", "adjust_inventory",
                "view_reports",
            ],
            "ACCOUNTANT": [
                "view_dashboard", "view_charges", "view_payments", "view_reports",
                "view_analytics", "view_accounting", "view_audit_logs",
            ],
            "SALES STAFF": [
                "view_dashboard", "view_crm", "view_analytics", "view_reservations",
                "view_guests",
            ],
            "STAFF": ["view_dashboard", "view_reservations", "view_guests"],
        }
        permissions = role_permissions.get(role, [])
        return "*" in permissions or permission in permissions


class RefreshToken(Base):
    """Refresh Token Model"""

    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(500), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)

    user = relationship("User")

    def __repr__(self):
        return f"<RefreshToken {self.id}>"

    def is_expired(self):
        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) > expires_at

    def is_valid(self):
        return not self.revoked and not self.is_expired()


class AuditLog(TenantScopedMixin, Base):
    """Audit Log Model"""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    username = Column(String(100), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    status = Column(String(20), nullable=False)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )

    def __repr__(self):
        return f"<AuditLog {self.action} by {self.username}>"
