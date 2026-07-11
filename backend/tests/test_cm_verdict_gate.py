import pytest
from uuid import uuid4
from app.cm.gates.pms_verdict_gate import PMSVerdictGate
from app.cm.models import ExternalEvent


@pytest.fixture
def mock_cm_db(mocker):
    mock_db = mocker.MagicMock()
    mock_session = mocker.MagicMock()
    mock_session.__enter__.return_value = mock_db
    mocker.patch("app.cm.gates.pms_verdict_gate.get_cm_db", return_value=mock_session)
    return mock_db


def test_pms_verdict_gate_not_found(mock_cm_db):
    mock_cm_db.query().filter().first.return_value = None
    gate = PMSVerdictGate()
    result = gate.execute(uuid4())
    assert result.success is False
    assert result.error_code == "NOT_FOUND"


def test_pms_verdict_gate_no_verdict(mock_cm_db):
    event = ExternalEvent(pms_verdict=None)
    mock_cm_db.query().filter().first.return_value = event
    gate = PMSVerdictGate()
    result = gate.execute(uuid4())
    assert result.success is False
    assert result.error_code == "NO_VERDICT"


def test_pms_verdict_gate_invalid_verdict(mock_cm_db):
    event = ExternalEvent(pms_verdict={"some_other_field": True})
    mock_cm_db.query().filter().first.return_value = event
    gate = PMSVerdictGate()
    result = gate.execute(uuid4())
    assert result.success is False
    assert result.error_code == "INVALID_VERDICT"


def test_pms_verdict_gate_success(mock_cm_db):
    event = ExternalEvent(
        idempotency_key="test_key", pms_verdict={"success": True, "reservation_id": 456}
    )
    mock_cm_db.query().filter().first.return_value = event

    gate = PMSVerdictGate()
    result = gate.execute(uuid4())

    assert result.success is True
    assert result.data["success"] is True
    assert result.data["reservation_id"] == 456

    # Check if the DB execute call was made to update idempotency records
    assert mock_cm_db.execute.called
