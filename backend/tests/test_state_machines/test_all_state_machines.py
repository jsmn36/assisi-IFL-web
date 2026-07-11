"""
Tests for all 6 lightweight state machines and the StateTransitionValidator.
"""
import pytest
from app.state_machines.base import (
    StateMachine,
    TransitionResult,
    InvalidStateTransitionError,
)
from app.state_machines.occupancy import OccupancyStateMachine
from app.state_machines.condition import ConditionStateMachine
from app.state_machines.reservation import ReservationLightStateMachine
from app.state_machines.stay import StayLightStateMachine
from app.state_machines.housekeeping_task import HousekeepingTaskStateMachine
from app.state_machines.day_close import DayCloseStateMachine
from app.state_machines.validator import StateTransitionValidator


# ── Base StateMachine ────────────────────────────────────────────────────


class TestBaseStateMachine:
    def test_empty_transitions_rejects_everything(self):
        sm = StateMachine()
        result = sm.can_transition("A", "B")
        assert not result.allowed

    def test_transition_result_dataclass(self):
        r = TransitionResult(allowed=True)
        assert r.allowed is True
        assert r.reason is None

    def test_validate_raises_on_invalid(self):
        sm = StateMachine()
        with pytest.raises(InvalidStateTransitionError):
            sm.validate("X", "Y")

    def test_is_terminal(self):
        sm = StateMachine()
        sm.transitions = {"A": {"B"}, "B": set()}
        assert not sm.is_terminal("A")
        assert sm.is_terminal("B")


# ── Occupancy ────────────────────────────────────────────────────────────


class TestOccupancyStateMachine:
    @pytest.fixture
    def sm(self):
        return OccupancyStateMachine()

    # Valid transitions
    def test_vacant_to_occupied(self, sm):
        assert sm.can_transition("VACANT", "OCCUPIED").allowed

    def test_vacant_to_blocked(self, sm):
        assert sm.can_transition("VACANT", "BLOCKED").allowed

    def test_occupied_to_vacant(self, sm):
        assert sm.can_transition("OCCUPIED", "VACANT").allowed

    def test_blocked_to_vacant(self, sm):
        assert sm.can_transition("BLOCKED", "VACANT").allowed

    # Invalid transitions
    def test_occupied_to_blocked_rejected(self, sm):
        result = sm.can_transition("OCCUPIED", "BLOCKED")
        assert not result.allowed

    def test_blocked_to_occupied_rejected(self, sm):
        result = sm.can_transition("BLOCKED", "OCCUPIED")
        assert not result.allowed

    def test_vacant_to_vacant_rejected(self, sm):
        result = sm.can_transition("VACANT", "VACANT")
        assert not result.allowed

    def test_validate_raises_on_invalid(self, sm):
        with pytest.raises(InvalidStateTransitionError):
            sm.validate("OCCUPIED", "BLOCKED")


# ── Condition ────────────────────────────────────────────────────────────


class TestConditionStateMachine:
    @pytest.fixture
    def sm(self):
        return ConditionStateMachine()

    # Valid transitions
    def test_clean_to_dirty(self, sm):
        assert sm.can_transition("CLEAN", "DIRTY").allowed

    def test_clean_to_out_of_service(self, sm):
        assert sm.can_transition("CLEAN", "OUT_OF_SERVICE").allowed

    def test_dirty_to_clean(self, sm):
        assert sm.can_transition("DIRTY", "CLEAN").allowed

    def test_dirty_to_inspected(self, sm):
        assert sm.can_transition("DIRTY", "INSPECTED").allowed

    def test_dirty_to_out_of_service(self, sm):
        assert sm.can_transition("DIRTY", "OUT_OF_SERVICE").allowed

    def test_inspected_to_clean(self, sm):
        assert sm.can_transition("INSPECTED", "CLEAN").allowed

    def test_inspected_to_dirty(self, sm):
        assert sm.can_transition("INSPECTED", "DIRTY").allowed

    def test_out_of_service_to_clean(self, sm):
        assert sm.can_transition("OUT_OF_SERVICE", "CLEAN").allowed

    # Invalid transitions
    def test_clean_to_inspected_rejected(self, sm):
        assert not sm.can_transition("CLEAN", "INSPECTED").allowed

    def test_out_of_service_to_dirty_rejected(self, sm):
        assert not sm.can_transition("OUT_OF_SERVICE", "DIRTY").allowed

    def test_inspected_to_out_of_service_rejected(self, sm):
        assert not sm.can_transition("INSPECTED", "OUT_OF_SERVICE").allowed


# ── Reservation ──────────────────────────────────────────────────────────


class TestReservationLightStateMachine:
    @pytest.fixture
    def sm(self):
        return ReservationLightStateMachine()

    # Valid transitions
    def test_tentative_to_confirmed(self, sm):
        assert sm.can_transition("TENTATIVE", "CONFIRMED").allowed

    def test_tentative_to_cancelled(self, sm):
        assert sm.can_transition("TENTATIVE", "CANCELLED").allowed

    def test_confirmed_to_checked_in(self, sm):
        assert sm.can_transition("CONFIRMED", "CHECKED_IN").allowed

    def test_confirmed_to_cancelled(self, sm):
        assert sm.can_transition("CONFIRMED", "CANCELLED").allowed

    def test_confirmed_to_no_show(self, sm):
        assert sm.can_transition("CONFIRMED", "NO_SHOW").allowed

    def test_checked_in_to_checked_out(self, sm):
        assert sm.can_transition("CHECKED_IN", "CHECKED_OUT").allowed

    # Legacy PENDING alias
    def test_pending_to_confirmed(self, sm):
        assert sm.can_transition("PENDING", "CONFIRMED").allowed

    def test_pending_to_cancelled(self, sm):
        assert sm.can_transition("PENDING", "CANCELLED").allowed

    # Terminal states
    def test_checked_out_is_terminal(self, sm):
        assert sm.is_terminal("CHECKED_OUT")

    def test_cancelled_is_terminal(self, sm):
        assert sm.is_terminal("CANCELLED")

    def test_no_show_is_terminal(self, sm):
        assert sm.is_terminal("NO_SHOW")

    # Invalid transitions
    def test_checked_out_to_checked_in_rejected(self, sm):
        assert not sm.can_transition("CHECKED_OUT", "CHECKED_IN").allowed

    def test_cancelled_to_confirmed_rejected(self, sm):
        assert not sm.can_transition("CANCELLED", "CONFIRMED").allowed

    def test_checked_in_to_confirmed_rejected(self, sm):
        assert not sm.can_transition("CHECKED_IN", "CONFIRMED").allowed


# ── Stay ─────────────────────────────────────────────────────────────────


class TestStayLightStateMachine:
    @pytest.fixture
    def sm(self):
        return StayLightStateMachine()

    def test_active_to_checked_out(self, sm):
        assert sm.can_transition("ACTIVE", "CHECKED_OUT").allowed

    def test_active_to_cancelled(self, sm):
        assert sm.can_transition("ACTIVE", "CANCELLED").allowed

    def test_checked_out_is_terminal(self, sm):
        assert sm.is_terminal("CHECKED_OUT")

    def test_cancelled_is_terminal(self, sm):
        assert sm.is_terminal("CANCELLED")

    def test_checked_out_to_active_rejected(self, sm):
        assert not sm.can_transition("CHECKED_OUT", "ACTIVE").allowed

    def test_cancelled_to_active_rejected(self, sm):
        assert not sm.can_transition("CANCELLED", "ACTIVE").allowed

    def test_active_to_active_rejected(self, sm):
        assert not sm.can_transition("ACTIVE", "ACTIVE").allowed


# ── Housekeeping Task ────────────────────────────────────────────────────


class TestHousekeepingTaskStateMachine:
    @pytest.fixture
    def sm(self):
        return HousekeepingTaskStateMachine()

    def test_pending_to_in_progress(self, sm):
        assert sm.can_transition("PENDING", "IN_PROGRESS").allowed

    def test_pending_to_done(self, sm):
        assert sm.can_transition("PENDING", "DONE").allowed

    def test_in_progress_to_done(self, sm):
        assert sm.can_transition("IN_PROGRESS", "DONE").allowed

    def test_in_progress_to_pending(self, sm):
        assert sm.can_transition("IN_PROGRESS", "PENDING").allowed

    def test_done_to_verified(self, sm):
        assert sm.can_transition("DONE", "VERIFIED").allowed

    def test_done_to_in_progress(self, sm):
        assert sm.can_transition("DONE", "IN_PROGRESS").allowed

    def test_verified_is_terminal(self, sm):
        assert sm.is_terminal("VERIFIED")

    def test_verified_to_done_rejected(self, sm):
        assert not sm.can_transition("VERIFIED", "DONE").allowed

    def test_pending_to_verified_rejected(self, sm):
        assert not sm.can_transition("PENDING", "VERIFIED").allowed


# ── Day Close ────────────────────────────────────────────────────────────


class TestDayCloseStateMachine:
    @pytest.fixture
    def sm(self):
        return DayCloseStateMachine()

    def test_open_to_closing(self, sm):
        assert sm.can_transition("OPEN", "CLOSING").allowed

    def test_closing_to_closed(self, sm):
        assert sm.can_transition("CLOSING", "CLOSED").allowed

    def test_closing_to_open(self, sm):
        assert sm.can_transition("CLOSING", "OPEN").allowed

    def test_closed_is_terminal(self, sm):
        assert sm.is_terminal("CLOSED")

    def test_open_to_closed_rejected(self, sm):
        assert not sm.can_transition("OPEN", "CLOSED").allowed

    def test_closed_to_open_rejected(self, sm):
        assert not sm.can_transition("CLOSED", "OPEN").allowed

    def test_closed_to_closing_rejected(self, sm):
        assert not sm.can_transition("CLOSED", "CLOSING").allowed


# ── StateTransitionValidator ─────────────────────────────────────────────


class TestStateTransitionValidator:
    @pytest.fixture
    def v(self):
        return StateTransitionValidator()

    def test_registered_machines(self, v):
        expected = {
            "occupancy",
            "condition",
            "reservation",
            "stay",
            "housekeeping_task",
            "day_close",
        }
        assert set(v.machines.keys()) == expected

    def test_validate_valid_transition(self, v):
        # Should not raise
        v.validate("occupancy", "VACANT", "OCCUPIED")

    def test_validate_invalid_transition_raises(self, v):
        with pytest.raises(InvalidStateTransitionError):
            v.validate("occupancy", "OCCUPIED", "BLOCKED")

    def test_validate_unknown_machine_raises_value_error(self, v):
        with pytest.raises(ValueError, match="Unknown state machine"):
            v.validate("nonexistent", "A", "B")

    def test_can_transition_returns_result(self, v):
        result = v.can_transition("condition", "CLEAN", "DIRTY")
        assert result.allowed is True

    def test_can_transition_unknown_machine(self, v):
        result = v.can_transition("nonexistent", "A", "B")
        assert result.allowed is False
        assert "Unknown" in result.reason

    def test_cross_machine_validation(self, v):
        """Verify several machines in sequence (simulates a check-in)."""
        v.validate("reservation", "CONFIRMED", "CHECKED_IN")
        v.validate("occupancy", "VACANT", "OCCUPIED")
        v.validate("stay", "ACTIVE", "CHECKED_OUT")  # future check-out
