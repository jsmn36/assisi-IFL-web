"""Localized tests for Phase 7 night audit / day close gate orchestration."""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from app.database import Base
import app.models  # noqa: F401 — register models

from app.models.property import Property
from app.models.business_day import BusinessDay
from app.models.enums import DayStatus
from app.models.room import Room, OccupancyState, ConditionState
from app.models.room_type import RoomType
from app.services.base_service import BusinessRuleError
from app.services.night_audit_service import NightAuditService
from app.services.business_day_service import BusinessDayService


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()

    Base.metadata.drop_all(bind=engine)


def _seed_property(db_session):
    prop = Property(name="Phase7 Hotel", code="P7H")
    db_session.add(prop)
    db_session.commit()
    db_session.refresh(prop)
    return prop


def test_run_night_audit_success_empty_property(db_session):
    prop = _seed_property(db_session)
    bd = BusinessDay(
        property_id=prop.id,
        business_date=date.today(),
        status=DayStatus.OPEN,
    )
    db_session.add(bd)
    db_session.commit()

    svc = NightAuditService(db_session)
    out = svc.run_night_audit(prop.id, date.today(), user_id=1)
    assert out["status"] == "success"
    db_session.refresh(bd)
    assert bd.night_audit_completed
    assert bd.status == DayStatus.CLOSING


def test_run_night_audit_respects_audit_date(db_session):
    prop = _seed_property(db_session)
    d = date.today() - timedelta(days=3)
    bd = BusinessDay(property_id=prop.id, business_date=d, status=DayStatus.OPEN)
    db_session.add(bd)
    db_session.commit()

    svc = NightAuditService(db_session)
    out = svc.run_night_audit(prop.id, d, user_id=1)
    assert out["status"] == "success"
    db_session.refresh(bd)
    assert bd.business_date == d
    assert bd.night_audit_completed


def test_close_business_day_after_night_audit(db_session):
    prop = _seed_property(db_session)
    bd = BusinessDay(
        property_id=prop.id,
        business_date=date.today(),
        status=DayStatus.CLOSING,
        night_audit_completed_at=datetime.now(timezone.utc),
    )
    db_session.add(bd)
    db_session.commit()

    bds = BusinessDayService(db_session)
    close_out = bds.close_business_day(prop.id, user_id=1)
    assert close_out["status"] == "success"
    db_session.refresh(bd)
    assert bd.status == DayStatus.CLOSED


def test_business_day_night_audit_completed_property(db_session):
    bd = BusinessDay()
    assert bd.night_audit_completed is False
    assert hasattr(bd, "night_audit_completed")


def test_start_night_audit_service(db_session):
    prop = _seed_property(db_session)
    bd = BusinessDay(
        property_id=prop.id,
        business_date=date.today(),
        status=DayStatus.OPEN,
    )
    db_session.add(bd)
    db_session.commit()

    bds = BusinessDayService(db_session)
    out = bds.start_night_audit(prop.id, date.today(), user_id=1)
    assert out["status"] == "success"
    db_session.refresh(bd)
    assert bd.status == DayStatus.IN_AUDIT


def _seed_property_with_dirty_vacant_room(db_session):
    """Property + one vacant/dirty room (fails NightAudit check 5)."""
    prop = _seed_property(db_session)
    rt = RoomType(
        property_id=prop.id,
        name="Standard",
        code="STD",
        base_price=Decimal("120"),
    )
    db_session.add(rt)
    db_session.commit()
    db_session.refresh(rt)
    room = Room(
        property_id=prop.id,
        room_type_id=rt.id,
        room_number="101",
        occupancy_state=OccupancyState.VACANT,
        condition_state=ConditionState.DIRTY,
    )
    db_session.add(room)
    db_session.commit()
    return prop


def test_run_night_audit_failure_dirty_vacant_room(db_session):
    prop = _seed_property_with_dirty_vacant_room(db_session)
    biz = date.today()
    bd = BusinessDay(property_id=prop.id, business_date=biz, status=DayStatus.OPEN)
    db_session.add(bd)
    db_session.commit()

    svc = NightAuditService(db_session)
    out = svc.run_night_audit(prop.id, biz, user_id=1)
    assert out["status"] == "failed"
    assert "dirty" in out["error"].lower() or "Check 5" in out["error"]


def test_run_night_audit_failed_transaction_rolls_back(db_session):
    prop = _seed_property_with_dirty_vacant_room(db_session)
    biz = date.today()
    bd = BusinessDay(property_id=prop.id, business_date=biz, status=DayStatus.OPEN)
    db_session.add(bd)
    db_session.commit()
    bd_id = bd.id

    svc = NightAuditService(db_session)
    out = svc.run_night_audit(prop.id, biz, user_id=1)
    assert out["status"] == "failed"

    db_session.expire_all()
    bd_again = db_session.query(BusinessDay).filter(BusinessDay.id == bd_id).one()
    assert bd_again.status == DayStatus.OPEN
    assert bd_again.night_audit_completed_at is None


def test_run_night_audit_skipped_when_business_day_closed(db_session):
    prop = _seed_property(db_session)
    biz = date.today()
    bd = BusinessDay(
        property_id=prop.id,
        business_date=biz,
        status=DayStatus.CLOSED,
        is_closed=True,
    )
    db_session.add(bd)
    db_session.commit()

    svc = NightAuditService(db_session)
    out = svc.run_night_audit(prop.id, biz, user_id=1)
    assert out["status"] == "skipped"
    assert "closed" in out["message"].lower()


def test_run_night_audit_date_alignment_only_updates_target_row(db_session):
    prop = _seed_property(db_session)
    d_target = date.today() - timedelta(days=4)
    d_other = date.today() - timedelta(days=2)
    bd_target = BusinessDay(
        property_id=prop.id,
        business_date=d_target,
        status=DayStatus.OPEN,
    )
    bd_other = BusinessDay(
        property_id=prop.id,
        business_date=d_other,
        status=DayStatus.OPEN,
    )
    db_session.add_all([bd_target, bd_other])
    db_session.commit()

    svc = NightAuditService(db_session)
    out = svc.run_night_audit(prop.id, d_target, user_id=1)
    assert out["status"] == "success"

    db_session.refresh(bd_target)
    db_session.refresh(bd_other)
    assert bd_target.night_audit_completed
    assert bd_target.status == DayStatus.CLOSING
    assert not bd_other.night_audit_completed
    assert bd_other.status == DayStatus.OPEN


def test_close_business_day_raises_when_no_closing_row(db_session):
    prop = _seed_property(db_session)
    bd = BusinessDay(
        property_id=prop.id,
        business_date=date.today(),
        status=DayStatus.OPEN,
    )
    db_session.add(bd)
    db_session.commit()

    bds = BusinessDayService(db_session)
    with pytest.raises(BusinessRuleError) as excinfo:
        bds.close_business_day(prop.id, user_id=1)
    assert "closing" in str(excinfo.value).lower()


def test_close_business_day_raises_when_night_audit_not_complete(db_session):
    prop = _seed_property(db_session)
    bd = BusinessDay(
        property_id=prop.id,
        business_date=date.today(),
        status=DayStatus.CLOSING,
        night_audit_completed_at=None,
    )
    db_session.add(bd)
    db_session.commit()

    bds = BusinessDayService(db_session)
    with pytest.raises(BusinessRuleError) as excinfo:
        bds.close_business_day(prop.id, user_id=1)
    assert "night audit" in str(excinfo.value).lower()


def test_start_night_audit_raises_for_missing_business_day_date(db_session):
    prop = _seed_property(db_session)
    bd = BusinessDay(
        property_id=prop.id,
        business_date=date.today(),
        status=DayStatus.OPEN,
    )
    db_session.add(bd)
    db_session.commit()

    missing_date = date.today() - timedelta(days=20)
    bds = BusinessDayService(db_session)
    with pytest.raises(BusinessRuleError) as excinfo:
        bds.start_night_audit(prop.id, missing_date, user_id=1)
    assert (
        "business day" in str(excinfo.value).lower()
        or "no business day" in str(excinfo.value).lower()
    )


def test_close_business_day_picks_newest_closing_row_by_date(db_session):
    """Multiple CLOSING rows: service should close the latest business_date."""
    prop = _seed_property(db_session)
    older = date.today() - timedelta(days=3)
    newer = date.today() - timedelta(days=1)
    completed_at = datetime.now(timezone.utc)
    bd_old = BusinessDay(
        property_id=prop.id,
        business_date=older,
        status=DayStatus.CLOSING,
        night_audit_completed_at=completed_at,
    )
    bd_new = BusinessDay(
        property_id=prop.id,
        business_date=newer,
        status=DayStatus.CLOSING,
        night_audit_completed_at=completed_at,
    )
    db_session.add_all([bd_old, bd_new])
    db_session.commit()

    bds = BusinessDayService(db_session)
    close_out = bds.close_business_day(prop.id, user_id=1)
    assert close_out["status"] == "success"

    db_session.refresh(bd_old)
    db_session.refresh(bd_new)
    assert bd_new.status == DayStatus.CLOSED
    assert bd_old.status == DayStatus.CLOSING
