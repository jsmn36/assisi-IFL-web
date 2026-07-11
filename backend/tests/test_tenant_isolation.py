"""Tenant isolation harness — Phase 2 acceptance gate.

Seeds two tenants in an in-memory SQLite DB, populates each with one of
every tenant-scoped row type, and asserts that:

  1. With tenant context = A, queries return only A rows.
  2. With tenant context = B, queries return only B rows.
  3. With no tenant context (e.g. unauthenticated boot), queries return all
     rows — but no production endpoint runs without a tenant set, so this
     branch is the safety hatch for migrations/scripts.
  4. New rows inserted under tenant A are auto-stamped with tenant_id=A.
  5. Even with a crafted ``WHERE property_id = <other-tenant-prop>`` clause,
     A's session returns zero rows from B.

This is the single most important test in the multi-tenant rollout: a
regression here means silent cross-tenant data leakage.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.tenant_context import bypass_tenant_filter, tenant_scope
from app.db.base import Base
from app.models import (
    AuditLog,
    Charge,
    Guest,
    HousekeepingTask,
    Notification,
    Property,
    RatePlan,
    Reservation,
    Room,
    RoomType,
    Stay,
    Tenant,
    User,
    UserTenant,
)
from app.models.enums import GuestType, ReservationSource, ReservationStatus

# Force-import: ensures every model with TenantScopedMixin is registered on
# Base.metadata before create_all runs.
import app.models  # noqa: F401


# ─── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture(scope="function")
def isolated_engine():
    """Fresh in-memory SQLite per test; multi-tenant scoped tables created."""
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def isolated_session(isolated_engine):
    Session = sessionmaker(bind=isolated_engine, autocommit=False, autoflush=False)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def two_tenants(isolated_session):
    """Seed tenants A and B with one of every tenant-scoped row type."""
    db = isolated_session

    with bypass_tenant_filter():
        tenant_a = Tenant(slug="alpha", name="Alpha Hotel Group", plan="standard")
        tenant_b = Tenant(slug="bravo", name="Bravo Resorts", plan="standard")
        db.add_all([tenant_a, tenant_b])
        db.flush()

        # Seed identical-shape data per tenant
        seeds = {}
        for tag, tenant in [("A", tenant_a), ("B", tenant_b)]:
            user = User(
                username=f"user_{tag.lower()}",
                email=f"{tag.lower()}@test",
                hashed_password="x",
                role="admin",
            )
            db.add(user)
            db.flush()

            membership = UserTenant(
                user_id=user.id,
                tenant_id=tenant.id,
                role="admin",
                is_default=True,
            )
            db.add(membership)

            prop = Property(
                tenant_id=tenant.id,
                name=f"Property {tag}",
                code=f"P{tag}",
                is_active=True,
            )
            db.add(prop)
            db.flush()

            room_type = RoomType(
                tenant_id=tenant.id,
                property_id=prop.id,
                name=f"RoomType {tag}",
                code=f"RT{tag}",
                base_price=Decimal("100.00"),
            )
            db.add(room_type)
            db.flush()

            room = Room(
                tenant_id=tenant.id,
                property_id=prop.id,
                room_type_id=room_type.id,
                room_number=f"{tag}101",
            )
            db.add(room)
            db.flush()

            guest = Guest(
                tenant_id=tenant.id,
                first_name=f"Guest{tag}",
                last_name="Test",
                email=f"guest_{tag.lower()}@test.com",
                guest_type=GuestType.INDIVIDUAL,
                property_id=prop.id,
            )
            db.add(guest)
            db.flush()

            rate_plan = RatePlan(
                tenant_id=tenant.id,
                property_id=prop.id,
                room_type_id=room_type.id,
                name=f"Rack {tag}",
                code=f"RACK{tag}",
                base_rate=Decimal("100.00"),
            )
            db.add(rate_plan)
            db.flush()

            reservation = Reservation(
                tenant_id=tenant.id,
                property_id=prop.id,
                guest_id=guest.id,
                room_id=room.id,
                room_type_id=room_type.id,
                rate_plan_id=rate_plan.id,
                confirmation_number=f"CONF-{tag}-001",
                check_in_date=date.today(),
                check_out_date=date.today() + timedelta(days=2),
                status=ReservationStatus.CONFIRMED,
                source=ReservationSource.DIRECT,
            )
            db.add(reservation)
            db.flush()

            audit = AuditLog(
                tenant_id=tenant.id,
                username=f"user_{tag.lower()}",
                action=f"seed_{tag}",
                resource_type="test",
                status="success",
            )
            db.add(audit)
            db.flush()

            seeds[tag] = dict(
                tenant=tenant,
                user=user,
                property=prop,
                room=room,
                room_type=room_type,
                guest=guest,
                rate_plan=rate_plan,
                reservation=reservation,
                audit=audit,
            )

        db.commit()

    return seeds


# ─── Tests ─────────────────────────────────────────────────────────────────


SCOPED_MODELS = [Property, Room, RoomType, Guest, Reservation, RatePlan, AuditLog]


def test_no_cross_tenant_leak_on_select(isolated_session, two_tenants):
    """Tenant A's session sees only A rows for every scoped model."""
    db = isolated_session
    a_tid = two_tenants["A"]["tenant"].id
    b_tid = two_tenants["B"]["tenant"].id
    assert a_tid != b_tid

    with tenant_scope(a_tid):
        for model in SCOPED_MODELS:
            rows = db.query(model).all()
            assert all(r.tenant_id == a_tid for r in rows), (
                f"{model.__name__} leaked tenant {b_tid} into tenant {a_tid} session"
            )

    with tenant_scope(b_tid):
        for model in SCOPED_MODELS:
            rows = db.query(model).all()
            assert all(r.tenant_id == b_tid for r in rows), (
                f"{model.__name__} leaked tenant {a_tid} into tenant {b_tid} session"
            )


def test_crafted_filter_cannot_bypass(isolated_session, two_tenants):
    """Even with a deliberate ``filter(property_id=other_tenant_prop)`` an
    A-context query returns zero rows because the row-filter clamps to A.
    """
    db = isolated_session
    a_tid = two_tenants["A"]["tenant"].id
    b_prop_id = two_tenants["B"]["property"].id

    with tenant_scope(a_tid):
        rooms = db.query(Room).filter(Room.property_id == b_prop_id).all()
        assert rooms == []

        reservations = (
            db.query(Reservation).filter(Reservation.property_id == b_prop_id).all()
        )
        assert reservations == []


def test_insert_autostamps_tenant_id(isolated_session, two_tenants):
    """Inserts under tenant context A get tenant_id = A automatically."""
    db = isolated_session
    a_tid = two_tenants["A"]["tenant"].id
    a_prop = two_tenants["A"]["property"]
    a_room_type = two_tenants["A"]["room_type"]

    with tenant_scope(a_tid):
        room = Room(
            property_id=a_prop.id,
            room_type_id=a_room_type.id,
            room_number="A999",
        )
        db.add(room)
        db.flush()
        # No explicit tenant_id passed; before_flush hook sets it.
        assert room.tenant_id == a_tid


def test_bypass_returns_all_rows(isolated_session, two_tenants):
    """The bypass helper is the migration/admin escape hatch — both
    tenants visible at once. Fail-safe pattern: we want to be able to
    confirm both tenants exist."""
    db = isolated_session
    with bypass_tenant_filter():
        rooms = db.query(Room).all()
        tenant_ids = {r.tenant_id for r in rooms}
    assert {two_tenants["A"]["tenant"].id, two_tenants["B"]["tenant"].id} <= tenant_ids


def test_no_tenant_context_no_filter(isolated_session, two_tenants):
    """When no tenant is set the filter is skipped — used by Alembic and
    pre-auth code paths. Production handlers will never hit this branch
    because the tenant middleware sets a value or rejects the request."""
    db = isolated_session
    # The autouse conftest fixture sets tenant_scope(1) for every test;
    # opt out here by setting the context to None so we exercise the
    # "no tenant" branch.
    with tenant_scope(None):
        rooms = db.query(Room).all()
    tenant_ids = {r.tenant_id for r in rooms}
    assert {two_tenants["A"]["tenant"].id, two_tenants["B"]["tenant"].id} <= tenant_ids


def test_tenant_scope_isolates_writes(isolated_session, two_tenants):
    """Switching scopes correctly isolates new writes."""
    db = isolated_session
    a_tid = two_tenants["A"]["tenant"].id
    b_tid = two_tenants["B"]["tenant"].id
    a_prop = two_tenants["A"]["property"]
    a_room_type = two_tenants["A"]["room_type"]
    b_prop = two_tenants["B"]["property"]
    b_room_type = two_tenants["B"]["room_type"]

    with tenant_scope(a_tid):
        db.add(
            Room(
                property_id=a_prop.id,
                room_type_id=a_room_type.id,
                room_number="A_NEW",
            )
        )
        db.commit()

    with tenant_scope(b_tid):
        db.add(
            Room(
                property_id=b_prop.id,
                room_type_id=b_room_type.id,
                room_number="B_NEW",
            )
        )
        db.commit()

    with tenant_scope(a_tid):
        a_rooms = db.query(Room).all()
        assert any(r.room_number == "A_NEW" for r in a_rooms)
        assert not any(r.room_number == "B_NEW" for r in a_rooms)

    with tenant_scope(b_tid):
        b_rooms = db.query(Room).all()
        assert any(r.room_number == "B_NEW" for r in b_rooms)
        assert not any(r.room_number == "A_NEW" for r in b_rooms)
