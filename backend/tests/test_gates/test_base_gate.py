import pytest
from typing import Dict, Any
from app.gates.base_gate import BaseGate, GateResult, GateStatus


class TestGate(BaseGate):
    """Test gate implementation"""

    @property
    def gate_name(self) -> str:
        return "test_gate"

    @property
    def description(self) -> str:
        return "Test gate for unit testing"

    def validate(self, context: Dict[str, Any]) -> GateResult:
        # Simple validation: check if "should_pass" is True
        if context.get("should_pass", False):
            return self._pass("Test passed")
        else:
            return self._fail("Test failed")


# -----------------------
# GateResult Tests
# -----------------------


def test_gate_result_creation():
    """Test creating gate results"""
    result = GateResult(gate_name="test", status=GateStatus.PASSED, message="Success")

    assert result.gate_name == "test"
    assert result.status == GateStatus.PASSED
    assert result.passed is True
    assert result.failed is False


def test_gate_result_failed():
    """Test failed gate result"""
    result = GateResult(
        gate_name="test",
        status=GateStatus.FAILED,
        message="Validation failed",
        blocking=True,
    )

    assert result.failed is True
    assert result.passed is False
    assert result.should_block is True


def test_gate_result_warning():
    """Test warning gate result"""
    result = GateResult(
        gate_name="test",
        status=GateStatus.WARNING,
        message="Warning message",
        blocking=False,
    )

    assert result.status == GateStatus.WARNING
    assert result.should_block is False


# -----------------------
# BaseGate Execution Tests
# -----------------------


def test_gate_execution_pass():
    """Test gate execution that passes"""
    gate = TestGate()
    context = {"should_pass": True}

    result = gate.execute(context)

    assert result.passed is True
    assert result.gate_name == "test_gate"


def test_gate_execution_fail():
    """Test gate execution that fails"""
    gate = TestGate()
    context = {"should_pass": False}

    result = gate.execute(context)

    assert result.failed is True
    assert result.should_block is True


def test_gate_blocking_vs_non_blocking():
    """Test blocking vs non-blocking gates"""
    blocking_gate = TestGate(blocking=True)
    non_blocking_gate = TestGate(blocking=False)

    context = {"should_pass": False}

    blocking_result = blocking_gate.execute(context)
    non_blocking_result = non_blocking_gate.execute(context)

    assert blocking_result.should_block is True
    assert non_blocking_result.should_block is False


def test_gate_result_to_dict():
    """Test converting gate result to dictionary"""
    result = GateResult(
        gate_name="test",
        status=GateStatus.PASSED,
        message="Success",
        details={"key": "value"},
    )

    result_dict = result.to_dict()

    assert result_dict["gate_name"] == "test"
    assert result_dict["status"] == "passed"
    assert result_dict["message"] == "Success"
    assert result_dict["details"]["key"] == "value"
