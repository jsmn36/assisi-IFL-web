"""
Tests for the Phase 4 Gate Framework Core:
  - GateExecutor lifecycle
  - TransactionCoordinator atomic sequences
"""
import pytest
from unittest.mock import MagicMock, patch
from app.gates.base import (
    BaseGate,
    GateContext,
    GateError,
    ValidationResult,
    ExecutionResult,
)
from app.gates.executor import GateExecutor
from app.gates.coordinator import TransactionCoordinator


# ── Helpers ──────────────────────────────────────────────────────────────


class SuccessGate(BaseGate):
    """Gate that always succeeds."""

    name = "SuccessGate"

    def pre_check(self, ctx: GateContext) -> ValidationResult:
        return ValidationResult(valid=True)

    def execute(self, ctx: GateContext) -> ExecutionResult:
        ctx.metadata["created"] = True
        return ExecutionResult(success=True, data={"id": 42})

    def post_check(self, ctx: GateContext) -> bool:
        return True

    def rollback(self, ctx: GateContext) -> None:
        ctx.metadata["rolled_back"] = True


class PreCheckFailGate(BaseGate):
    """Gate whose pre_check always fails."""

    name = "PreCheckFailGate"

    def pre_check(self, ctx: GateContext) -> ValidationResult:
        v = ValidationResult()
        v.add_error("missing field X")
        v.add_error("invalid date")
        return v

    def execute(self, ctx: GateContext) -> ExecutionResult:
        raise AssertionError("execute should not be called")

    def post_check(self, ctx: GateContext) -> bool:
        raise AssertionError("post_check should not be called")

    def rollback(self, ctx: GateContext) -> None:
        pass


class ExecuteFailGate(BaseGate):
    """Gate whose execute raises an exception."""

    name = "ExecuteFailGate"

    def pre_check(self, ctx: GateContext) -> ValidationResult:
        return ValidationResult(valid=True)

    def execute(self, ctx: GateContext) -> ExecutionResult:
        ctx.metadata["before_error"] = True
        raise RuntimeError("DB constraint violated")

    def post_check(self, ctx: GateContext) -> bool:
        return True

    def rollback(self, ctx: GateContext) -> None:
        ctx.metadata["rolled_back"] = True


class ExecuteReturnFailGate(BaseGate):
    """Gate whose execute returns success=False."""

    name = "ExecuteReturnFailGate"

    def pre_check(self, ctx: GateContext) -> ValidationResult:
        return ValidationResult(valid=True)

    def execute(self, ctx: GateContext) -> ExecutionResult:
        return ExecutionResult(success=False, error="insufficient balance")

    def post_check(self, ctx: GateContext) -> bool:
        return True

    def rollback(self, ctx: GateContext) -> None:
        ctx.metadata["rolled_back"] = True


class PostCheckFailGate(BaseGate):
    """Gate whose post_check returns False."""

    name = "PostCheckFailGate"

    def pre_check(self, ctx: GateContext) -> ValidationResult:
        return ValidationResult(valid=True)

    def execute(self, ctx: GateContext) -> ExecutionResult:
        return ExecutionResult(success=True, data={"ok": True})

    def post_check(self, ctx: GateContext) -> bool:
        return False

    def rollback(self, ctx: GateContext) -> None:
        ctx.metadata["rolled_back"] = True


class PostCheckRaiseGate(BaseGate):
    """Gate whose post_check raises an exception."""

    name = "PostCheckRaiseGate"

    def pre_check(self, ctx: GateContext) -> ValidationResult:
        return ValidationResult(valid=True)

    def execute(self, ctx: GateContext) -> ExecutionResult:
        return ExecutionResult(success=True, data={"ok": True})

    def post_check(self, ctx: GateContext) -> bool:
        raise RuntimeError("postcondition check blew up")

    def rollback(self, ctx: GateContext) -> None:
        ctx.metadata["rolled_back"] = True


class RollbackFailGate(BaseGate):
    """Gate whose rollback also raises."""

    name = "RollbackFailGate"

    def pre_check(self, ctx: GateContext) -> ValidationResult:
        return ValidationResult(valid=True)

    def execute(self, ctx: GateContext) -> ExecutionResult:
        raise RuntimeError("boom")

    def post_check(self, ctx: GateContext) -> bool:
        return True

    def rollback(self, ctx: GateContext) -> None:
        raise RuntimeError("rollback also boom")


def _make_context(**kwargs):
    return GateContext(
        db=MagicMock(),
        user_id=1,
        payload=kwargs,
    )


# ── GateExecutor tests ──────────────────────────────────────────────────


class TestGateExecutor:
    @pytest.fixture
    def executor(self):
        return GateExecutor()

    def test_happy_path(self, executor):
        ctx = _make_context()
        result = executor.run(SuccessGate(), ctx)
        assert result["id"] == 42
        assert ctx.metadata["created"] is True

    def test_pre_check_fails(self, executor):
        ctx = _make_context()
        with pytest.raises(GateError) as exc_info:
            executor.run(PreCheckFailGate(), ctx)
        assert "pre-check failed" in str(exc_info.value)
        assert len(exc_info.value.errors) == 2

    def test_execute_raises_triggers_rollback(self, executor):
        ctx = _make_context()
        with pytest.raises(GateError) as exc_info:
            executor.run(ExecuteFailGate(), ctx)
        assert "execute failed" in str(exc_info.value)
        assert ctx.metadata.get("rolled_back") is True

    def test_execute_returns_failure_triggers_rollback(self, executor):
        ctx = _make_context()
        with pytest.raises(GateError) as exc_info:
            executor.run(ExecuteReturnFailGate(), ctx)
        assert "execution failed" in str(exc_info.value)
        assert ctx.metadata.get("rolled_back") is True

    def test_post_check_returns_false_triggers_rollback(self, executor):
        ctx = _make_context()
        with pytest.raises(GateError) as exc_info:
            executor.run(PostCheckFailGate(), ctx)
        assert "post-check failed" in str(exc_info.value)
        assert ctx.metadata.get("rolled_back") is True

    def test_post_check_raises_triggers_rollback(self, executor):
        ctx = _make_context()
        with pytest.raises(GateError) as exc_info:
            executor.run(PostCheckRaiseGate(), ctx)
        assert "post-check raised" in str(exc_info.value)
        assert ctx.metadata.get("rolled_back") is True

    def test_rollback_failure_still_raises_original_error(self, executor):
        ctx = _make_context()
        with pytest.raises(GateError) as exc_info:
            executor.run(RollbackFailGate(), ctx)
        # The original execute error should propagate
        assert "execute failed" in str(exc_info.value)


# ── TransactionCoordinator tests ─────────────────────────────────────────


class TestTransactionCoordinator:
    @pytest.fixture
    def coordinator(self):
        return TransactionCoordinator()

    def test_two_gates_succeed(self, coordinator):
        db = MagicMock()
        result = coordinator.run_sequence(
            gates=[
                (SuccessGate(), {"step": 1}),
                (SuccessGate(), {"step": 2}),
            ],
            db=db,
            user_id=1,
        )
        assert result["id"] == 42
        db.commit.assert_called_once()

    def test_second_gate_fails_rollback(self, coordinator):
        db = MagicMock()
        with pytest.raises(GateError):
            coordinator.run_sequence(
                gates=[
                    (SuccessGate(), {}),
                    (ExecuteFailGate(), {}),
                ],
                db=db,
                user_id=1,
            )
        db.rollback.assert_called_once()
        db.commit.assert_not_called()

    def test_gate_error_propagated_with_message(self, coordinator):
        db = MagicMock()
        with pytest.raises(GateError) as exc_info:
            coordinator.run_sequence(
                gates=[(PreCheckFailGate(), {})],
                db=db,
                user_id=1,
            )
        assert "pre-check failed" in str(exc_info.value)

    def test_empty_sequence_commits(self, coordinator):
        db = MagicMock()
        result = coordinator.run_sequence(gates=[], db=db)
        assert result == {}
        db.commit.assert_called_once()
