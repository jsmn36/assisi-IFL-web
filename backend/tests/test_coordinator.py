import pytest
from unittest.mock import Mock, MagicMock
from app.core.transaction_coordinator import TransactionCoordinator
from app.gates.base_gate import BaseGate, GateResult, GateStatus


class DummyPassGate(BaseGate):
    name = "dummy_pass"

    @property
    def gate_name(self):
        return self.name

    @property
    def description(self):
        return "Passes"

    def validate(self, context, db):
        return self._pass("passed")


class DummyFailGate(BaseGate):
    name = "dummy_fail"

    @property
    def gate_name(self):
        return self.name

    @property
    def description(self):
        return "Fails"

    def validate(self, context, db):
        return self._fail("failed")


def test_coordinator_passes_and_commits():
    # Setup
    db = MagicMock()
    tc = TransactionCoordinator(db)

    action_called = False

    def my_action(session):
        nonlocal action_called
        action_called = True

    gates = [DummyPassGate()]

    # Execute
    success, result = tc.execute_write(gates, {}, my_action)

    # Assertions
    assert success is True
    assert action_called is True
    # One commit from the Gate history recording, one from Coordinator
    assert db.commit.call_count >= 2
    assert result.has_blocking_failures is False


def test_coordinator_fails_gate_and_aborts():
    # Setup
    db = MagicMock()
    tc = TransactionCoordinator(db)

    action_called = False

    def my_action(session):
        nonlocal action_called
        action_called = True

    gates = [DummyPassGate(), DummyFailGate()]  # Fails

    # Execute
    success, result = tc.execute_write(gates, {}, my_action)

    # Assertions
    assert success is False
    assert action_called is False  # Action should NEVER be called
    # Coordinator explicit rollback triggered due to execution bounds
    assert db.rollback.call_count >= 1
    assert result.has_blocking_failures is True


def test_coordinator_action_exception_rollbacks():
    # Setup
    db = MagicMock()
    tc = TransactionCoordinator(db)

    def my_failing_action(session):
        raise ValueError("Simulated DB Insert Failure")

    gates = [DummyPassGate()]

    # Execute
    with pytest.raises(ValueError):
        tc.execute_write(gates, {}, my_failing_action)

    # Assertions
    assert db.rollback.call_count >= 1
