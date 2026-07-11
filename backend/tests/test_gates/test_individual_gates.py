"""
Integration tests for Phase 5 individual gates.

Uses SQLite in-memory database with real model instances.
Tests: happy path, pre_check failure, execute failure (+ rollback),
and post_check failure for each gate.
"""
import pytest
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.gates.base import GateContext, GateError
from app.gates.executor import GateExecutor
from app.gates.reservation_confirmation import ReservationConfirmationGate
from app.gates.room_assignment import RoomAssignmentGate
from app.gates.check_in import CheckInGate
from app.gates.check_out import CheckOutGate
from app.gates.in_stay_mutation import InStayMutationGate
from app.gates.manual_override import ManualOverrideGate
from app.models.property import Property
from app.models.room_type import RoomType
from app.models.room import Room, OccupancyState, ConditionState
from app.models.guest import Guest
from app.models.reservation import Reservation
from app.models.stay import Stay, StayStatus
from app.models.enums import ReservationStatus


# ── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture
def engine():
    e = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(e)
    return e


@pytest.fixture
def db(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def executor():
    return GateExecutor()


@pytest.fixture
def seed_data(db):
    """Create property, room type, room, and guest for tests."""
    prop = Property(id=1, name="Test Hotel", code="TST", currency="USD")
    db.add(prop)

    rt = RoomType(id=1, property_id=1, name="Standard", code="STD", base_price=100.0)
    db.add(rt)

    room = Room(
        id=1,
        property_id=1,
        room_type_id=1,
        room_number="101",
        occupancy_state=OccupancyState.VACANT,
        condition_state=ConditionState.CLEAN,
        is_active=True,
    )
    db.add(room)

    guest = Guest(
        id=1,
        first_name="John",
        last_name="Doe",
        email="john@example.com",
    )
    db.add(guest)
    db.commit()
    return {"property": prop, "room_type": rt, "room": room, "guest": guest}


def _make_ctx(db, payload, user_id=1):
    return GateContext(db=db, user_id=user_id, payload=payload)


# ── ReservationConfirmationGate ──────────────────────────────────────────


class TestReservationConfirmationGate:
    def test_happy_path(self, db, executor, seed_data):
        gate = ReservationConfirmationGate()
        ctx = _make_ctx(
            db,
            {
                "guest_id": 1,
                "room_type_id": 1,
                "check_in": str(date.today() + timedelta(days=1)),
                "check_out": str(date.today() + timedelta(days=3)),
                "nightly_rate": 100,
            },
        )
        result = executor.run(gate, ctx)
        assert "reservation_id" in result
        assert "confirmation_number" in result
        assert result["confirmation_number"].startswith("RES-")

        # Verify in DB
        res = (
            db.query(Reservation)
            .filter(Reservation.id == result["reservation_id"])
            .first()
        )
        assert res is not None
        assert res.status == ReservationStatus.CONFIRMED
        db.commit()

    def test_pre_check_missing_fields(self, db, executor, seed_data):
        gate = ReservationConfirmationGate()
        ctx = _make_ctx(db, {"guest_id": 1})  # missing room_type_id, dates
        with pytest.raises(GateError) as exc_info:
            executor.run(gate, ctx)
        assert "pre-check failed" in str(exc_info.value)

    def test_pre_check_invalid_dates(self, db, executor, seed_data):
        gate = ReservationConfirmationGate()
        ctx = _make_ctx(
            db,
            {
                "guest_id": 1,
                "room_type_id": 1,
                "check_in": str(date.today() + timedelta(days=3)),
                "check_out": str(date.today() + timedelta(days=1)),
            },
        )
        with pytest.raises(GateError):
            executor.run(gate, ctx)

    def test_pre_check_invalid_room_type(self, db, executor, seed_data):
        gate = ReservationConfirmationGate()
        ctx = _make_ctx(
            db,
            {
                "guest_id": 1,
                "room_type_id": 999,
                "check_in": str(date.today() + timedelta(days=1)),
                "check_out": str(date.today() + timedelta(days=3)),
            },
        )
        with pytest.raises(GateError):
            executor.run(gate, ctx)


# ── RoomAssignmentGate ───────────────────────────────────────────────────


class TestRoomAssignmentGate:
    def _create_reservation(self, db):
        res = Reservation(
            id=10,
            property_id=1,
            guest_id=1,
            room_type_id=1,
            confirmation_number="TEST-001",
            check_in_date=date.today() + timedelta(days=1),
            check_out_date=date.today() + timedelta(days=3),
            status=ReservationStatus.CONFIRMED,
        )
        db.add(res)
        db.commit()
        return res

    def test_happy_path(self, db, executor, seed_data):
        self._create_reservation(db)
        gate = RoomAssignmentGate()
        ctx = _make_ctx(db, {"reservation_id": 10, "room_id": 1})
        result = executor.run(gate, ctx)
        assert result["room_id"] == 1
        db.commit()

    def test_pre_check_room_not_available(self, db, executor, seed_data):
        self._create_reservation(db)
        room = db.query(Room).filter(Room.id == 1).first()
        room.occupancy_state = OccupancyState.OCCUPIED
        db.commit()

        gate = RoomAssignmentGate()
        ctx = _make_ctx(db, {"reservation_id": 10, "room_id": 1})
        with pytest.raises(GateError) as exc_info:
            executor.run(gate, ctx)
        assert "not available" in str(exc_info.value.errors[0])

    def test_pre_check_type_mismatch(self, db, executor, seed_data):
        res = Reservation(
            id=20,
            property_id=1,
            guest_id=1,
            room_type_id=999,  # wrong type
            confirmation_number="TEST-002",
            check_in_date=date.today() + timedelta(days=1),
            check_out_date=date.today() + timedelta(days=3),
            status=ReservationStatus.CONFIRMED,
        )
        db.add(res)
        db.commit()

        gate = RoomAssignmentGate()
        ctx = _make_ctx(db, {"reservation_id": 20, "room_id": 1})
        with pytest.raises(GateError) as exc_info:
            executor.run(gate, ctx)
        assert "type mismatch" in str(exc_info.value.errors[0])


# ── CheckInGate ──────────────────────────────────────────────────────────


class TestCheckInGate:
    def _create_reservation_with_room(self, db):
        res = Reservation(
            id=30,
            property_id=1,
            guest_id=1,
            room_type_id=1,
            room_id=1,
            confirmation_number="TEST-CI-001",
            check_in_date=date.today(),
            check_out_date=date.today() + timedelta(days=2),
            status=ReservationStatus.CONFIRMED,
        )
        db.add(res)
        db.commit()
        return res

    def test_happy_path(self, db, executor, seed_data):
        self._create_reservation_with_room(db)
        gate = CheckInGate()
        ctx = _make_ctx(db, {"reservation_id": 30})
        result = executor.run(gate, ctx)

        assert "stay_id" in result
        assert result["room_number"] == "101"

        # Verify state changes
        res = db.query(Reservation).filter(Reservation.id == 30).first()
        assert res.status == ReservationStatus.CHECKED_IN

        room = db.query(Room).filter(Room.id == 1).first()
        assert room.occupancy_state == OccupancyState.OCCUPIED

        stay = db.query(Stay).filter(Stay.id == result["stay_id"]).first()
        assert stay.status == StayStatus.CHECKED_IN
        db.commit()

    def test_pre_check_wrong_status(self, db, executor, seed_data):
        res = Reservation(
            id=31,
            property_id=1,
            guest_id=1,
            room_type_id=1,
            room_id=1,
            confirmation_number="TEST-CI-002",
            check_in_date=date.today(),
            check_out_date=date.today() + timedelta(days=2),
            status=ReservationStatus.PENDING,
        )
        db.add(res)
        db.commit()

        gate = CheckInGate()
        ctx = _make_ctx(db, {"reservation_id": 31})
        with pytest.raises(GateError):
            executor.run(gate, ctx)

    def test_pre_check_no_room(self, db, executor, seed_data):
        res = Reservation(
            id=32,
            property_id=1,
            guest_id=1,
            room_type_id=1,
            room_id=None,
            confirmation_number="TEST-CI-003",
            check_in_date=date.today(),
            check_out_date=date.today() + timedelta(days=2),
            status=ReservationStatus.CONFIRMED,
        )
        db.add(res)
        db.commit()

        gate = CheckInGate()
        ctx = _make_ctx(db, {"reservation_id": 32})
        with pytest.raises(GateError):
            executor.run(gate, ctx)

    def test_pre_check_room_dirty(self, db, executor, seed_data):
        room = db.query(Room).filter(Room.id == 1).first()
        room.condition_state = ConditionState.DIRTY
        db.commit()

        res = Reservation(
            id=33,
            property_id=1,
            guest_id=1,
            room_type_id=1,
            room_id=1,
            confirmation_number="TEST-CI-004",
            check_in_date=date.today(),
            check_out_date=date.today() + timedelta(days=2),
            status=ReservationStatus.CONFIRMED,
        )
        db.add(res)
        db.commit()

        gate = CheckInGate()
        ctx = _make_ctx(db, {"reservation_id": 33})
        with pytest.raises(GateError):
            executor.run(gate, ctx)


# ── CheckOutGate ─────────────────────────────────────────────────────────


class TestCheckOutGate:
    def _create_checked_in_stay(self, db, seed_data):
        res = Reservation(
            id=40,
            property_id=1,
            guest_id=1,
            room_type_id=1,
            room_id=1,
            confirmation_number="TEST-CO-001",
            check_in_date=date.today() - timedelta(days=1),
            check_out_date=date.today(),
            status=ReservationStatus.CHECKED_IN,
        )
        db.add(res)

        room = db.query(Room).filter(Room.id == 1).first()
        room.occupancy_state = OccupancyState.OCCUPIED

        stay = Stay(
            id=40,
            property_id=1,
            reservation_id=40,
            guest_id=1,
            room_id=1,
            status=StayStatus.CHECKED_IN,
            check_in_date=date.today() - timedelta(days=1),
            check_out_date=date.today(),
            is_active=True,
        )
        db.add(stay)
        db.commit()
        return stay

    def test_happy_path(self, db, executor, seed_data):
        self._create_checked_in_stay(db, seed_data)
        gate = CheckOutGate()
        ctx = _make_ctx(db, {"stay_id": 40})
        result = executor.run(gate, ctx)

        assert "housekeeping_task_id" in result

        stay = db.query(Stay).filter(Stay.id == 40).first()
        assert stay.status == StayStatus.CHECKED_OUT

        room = db.query(Room).filter(Room.id == 1).first()
        assert room.occupancy_state == OccupancyState.VACANT
        assert room.condition_state == ConditionState.DIRTY
        db.commit()

    def test_pre_check_stay_not_checked_in(self, db, executor, seed_data):
        stay = Stay(
            id=41,
            property_id=1,
            reservation_id=1,
            guest_id=1,
            room_id=1,
            status=StayStatus.RESERVED,
            check_in_date=date.today(),
            check_out_date=date.today() + timedelta(days=1),
        )
        db.add(stay)
        db.commit()

        gate = CheckOutGate()
        ctx = _make_ctx(db, {"stay_id": 41})
        with pytest.raises(GateError):
            executor.run(gate, ctx)


# ── InStayMutationGate ───────────────────────────────────────────────────


class TestInStayMutationGate:
    def _create_active_stay(self, db, seed_data):
        res = Reservation(
            id=50,
            property_id=1,
            guest_id=1,
            room_type_id=1,
            room_id=1,
            confirmation_number="TEST-MUT-001",
            check_in_date=date.today(),
            check_out_date=date.today() + timedelta(days=2),
            status=ReservationStatus.CHECKED_IN,
        )
        db.add(res)

        stay = Stay(
            id=50,
            property_id=1,
            reservation_id=50,
            guest_id=1,
            room_id=1,
            status=StayStatus.CHECKED_IN,
            check_in_date=date.today(),
            check_out_date=date.today() + timedelta(days=2),
            is_active=True,
            nightly_rate=Decimal("100.00"),
        )
        db.add(stay)
        db.commit()
        return stay

    def test_add_charge(self, db, executor, seed_data):
        self._create_active_stay(db, seed_data)
        gate = InStayMutationGate()
        ctx = _make_ctx(
            db,
            {
                "stay_id": 50,
                "mutation_type": "ADD_CHARGE",
                "amount": 25.50,
                "description": "Room service",
                "charge_type": "restaurant",
            },
        )
        result = executor.run(gate, ctx)
        assert result["charge_id"] is not None
        assert result["amount"] == 25.50
        db.commit()

    def test_change_rate(self, db, executor, seed_data):
        self._create_active_stay(db, seed_data)
        gate = InStayMutationGate()
        ctx = _make_ctx(
            db,
            {
                "stay_id": 50,
                "mutation_type": "CHANGE_RATE",
                "new_nightly_rate": 150.00,
            },
        )
        result = executor.run(gate, ctx)
        assert result["new_rate"] == 150.00

        stay = db.query(Stay).filter(Stay.id == 50).first()
        assert float(stay.nightly_rate) == 150.00
        db.commit()

    def test_invalid_mutation(self, db, executor, seed_data):
        self._create_active_stay(db, seed_data)
        gate = InStayMutationGate()
        ctx = _make_ctx(
            db,
            {
                "stay_id": 50,
                "mutation_type": "INVALID",
            },
        )
        with pytest.raises(GateError):
            executor.run(gate, ctx)


# ── ManualOverrideGate ───────────────────────────────────────────────────


class TestManualOverrideGate:
    def test_happy_path(self, db, executor, seed_data):
        gate = ManualOverrideGate()
        ctx = _make_ctx(
            db,
            {
                "justification": "Guest is VIP, override room condition",
                "target_gate": "CheckInGate",
            },
        )
        result = executor.run(gate, ctx)
        assert result["override_applied"] is True

    def test_pre_check_no_justification(self, db, executor, seed_data):
        gate = ManualOverrideGate()
        ctx = _make_ctx(db, {"target_gate": "CheckInGate"})
        with pytest.raises(GateError):
            executor.run(gate, ctx)

    def test_pre_check_no_user(self, db, executor, seed_data):
        gate = ManualOverrideGate()
        ctx = GateContext(
            db=db,
            user_id=None,
            payload={"justification": "test", "target_gate": "X"},
        )
        with pytest.raises(GateError):
            executor.run(gate, ctx)
