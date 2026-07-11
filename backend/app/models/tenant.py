"""Tenant and UserTenant models.

A Tenant represents one customer of the SaaS (a hotel group or independent
operator). A Tenant may own multiple Properties. Users belong to Tenants
via the UserTenant join table — a single user may have different roles in
different tenants (e.g. admin in their own hotel group, accountant in a
client's tenant).
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


DEFAULT_TENANT_ID = 1
DEFAULT_TENANT_SLUG = "default"


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    plan = Column(String(50), nullable=False, default="standard")
    is_active = Column(Boolean, default=True, nullable=False)
    # Per-tenant locale, used by analytics/reporting and (eventually) i18n.
    locale = Column(String(10), nullable=False, default="en-US")

    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    memberships = relationship(
        "UserTenant",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Tenant {self.slug}>"


class UserTenant(Base):
    """User ↔ Tenant membership with a per-tenant role.

    The global ``User.role`` column is retained for backwards compatibility
    (the initial migration seeds each existing user with a UserTenant row
    using that role against the default tenant), but going forward the role
    that counts is the one on this membership.
    """

    __tablename__ = "user_tenants"
    __table_args__ = (
        UniqueConstraint("user_id", "tenant_id", name="uq_user_tenant"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=False, default="staff")
    is_default = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    tenant = relationship("Tenant", back_populates="memberships")
    user = relationship("User")

    def __repr__(self) -> str:
        return f"<UserTenant user_id={self.user_id} tenant_id={self.tenant_id} role={self.role}>"
