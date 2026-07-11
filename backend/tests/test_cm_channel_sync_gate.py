import pytest
import uuid
from app.cm.gates.channel_sync import ChannelSyncExecutionGate
from app.cm.models import ChannelSyncLog
from app.cm.database import get_cm_db


@pytest.fixture
def mock_cm_db(mocker):
    mock_db = mocker.MagicMock()
    mock_session = mocker.MagicMock()
    mock_session.__enter__.return_value = mock_db
    mocker.patch("app.cm.gates.channel_sync.get_cm_db", return_value=mock_session)
    return mock_db


def test_channel_sync_not_found(mock_cm_db):
    mock_cm_db.query().filter().first.return_value = None
    gate = ChannelSyncExecutionGate()
    result = gate.execute(uuid.uuid4())

    assert result.success is False
    assert result.error_code == "NOT_FOUND"


def test_channel_sync_invalid_status(mock_cm_db):
    log_entry = ChannelSyncLog(status="success")
    mock_cm_db.query().filter().first.return_value = log_entry

    gate = ChannelSyncExecutionGate()
    result = gate.execute(uuid.uuid4())

    assert result.success is False
    assert result.error_code == "INVALID_STATUS"


def test_channel_sync_max_retries(mock_cm_db):
    log_entry = ChannelSyncLog(status="failed", attempt_number=6)
    mock_cm_db.query().filter().first.return_value = log_entry

    gate = ChannelSyncExecutionGate()
    result = gate.execute(uuid.uuid4())

    assert result.success is False
    assert result.error_code == "MAX_RETRIES_EXCEEDED"
    assert log_entry.status == "abandoned"


def test_channel_sync_success(mock_cm_db, requests_mock):
    task_id = uuid.uuid4()
    log_entry = ChannelSyncLog(
        log_id=task_id,
        status="pending",
        channel="booking_com",
        attempt_number=1,
        request_payload={"test": "data"},
    )
    mock_cm_db.query().filter().first.return_value = log_entry

    requests_mock.post(
        "http://localhost:8000/mock/ota/booking_com/update",
        status_code=200,
        json={"status": "ok"},
    )

    gate = ChannelSyncExecutionGate()
    result = gate.execute(task_id)

    assert result.success is True
    assert log_entry.status == "success"
    assert log_entry.http_status_code == 200
    mock_cm_db.commit.assert_called()


def test_channel_sync_failure_retry(mock_cm_db, requests_mock):
    task_id = uuid.uuid4()
    log_entry = ChannelSyncLog(
        log_id=task_id,
        status="pending",
        channel="booking_com",
        attempt_number=1,
        request_payload={"test": "data"},
    )
    mock_cm_db.query().filter().first.return_value = log_entry

    requests_mock.post(
        "http://localhost:8000/mock/ota/booking_com/update", status_code=500
    )

    gate = ChannelSyncExecutionGate()
    result = gate.execute(task_id)

    assert result.success is False
    assert result.error_code == "SYNC_FAILED"
    assert log_entry.status == "failed"
    assert log_entry.attempt_number == 2
    mock_cm_db.commit.assert_called()


def test_channel_sync_failure_abandoned(mock_cm_db, requests_mock):
    task_id = uuid.uuid4()
    log_entry = ChannelSyncLog(
        log_id=task_id,
        status="failed",
        channel="booking_com",
        attempt_number=5,
        request_payload={"test": "data"},
    )
    mock_cm_db.query().filter().first.return_value = log_entry

    requests_mock.post(
        "http://localhost:8000/mock/ota/booking_com/update", status_code=500
    )

    gate = ChannelSyncExecutionGate()
    result = gate.execute(task_id)

    assert result.success is False
    assert result.error_code == "SYNC_FAILED"
    assert log_entry.status == "abandoned"
    assert log_entry.attempt_number == 6
    mock_cm_db.commit.assert_called()
