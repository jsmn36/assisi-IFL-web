"""
Tests for StateTransitionHistory model
Run: pytest tests/test_models/test_state_transition_history.py -v
"""
import pytest
import json
from datetime import datetime, timezone
from app.models import StateTransitionHistory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_sth(test_db, **kwargs):
    history = StateTransitionHistory(
        entity_type=kwargs.get("entity_type", "reservation"),
        entity_id=kwargs.get("entity_id", 1),
        from_state=kwargs.get("from_state", "pending"),
        to_state=kwargs.get("to_state", "confirmed"),
        transition_name=kwargs.get("transition_name", "confirm"),
        triggered_by=kwargs.get("triggered_by", "receptionist@hotel.com"),
        trigger_type=kwargs.get("trigger_type", "manual"),
        is_successful=kwargs.get("is_successful", True),
        error_message=kwargs.get("error_message", None),
        error_code=kwargs.get("error_code", None),
        notes=kwargs.get("notes", None),
        duration_in_state=kwargs.get("duration_in_state", None),
        context_data=kwargs.get("context_data", None),
    )
    test_db.add(history)
    test_db.commit()
    test_db.refresh(history)
    return history


# ---------------------------------------------------------------------------
# Creation
# ---------------------------------------------------------------------------


def test_create_state_transition_history(test_db):
    history = make_sth(test_db)
    assert history.id is not None
    assert history.entity_type == "reservation"
    assert history.from_state == "pending"
    assert history.to_state == "confirmed"
    assert history.is_successful is True


def test_initial_state_transition_null_from(test_db):
    history = make_sth(
        test_db, from_state=None, to_state="reserved", transition_name="create"
    )
    assert history.from_state is None
    assert history.to_state == "reserved"


def test_failed_transition(test_db):
    history = make_sth(
        test_db,
        from_state="pending",
        to_state="checked_in",
        transition_name="check_in",
        is_successful=False,
        error_message="Cannot check in without confirming first",
        error_code="INVALID_TRANSITION",
    )
    assert history.is_successful is False
    assert history.error_code == "INVALID_TRANSITION"
    assert history.error_message == "Cannot check in without confirming first"


def test_automatic_transition(test_db):
    history = make_sth(
        test_db,
        from_state="confirmed",
        to_state="no_show",
        trigger_type="automatic",
        triggered_by="night_audit_system",
    )
    assert history.trigger_type == "automatic"
    assert history.triggered_by == "night_audit_system"


def test_scheduled_transition(test_db):
    history = make_sth(test_db, trigger_type="scheduled")
    assert history.trigger_type == "scheduled"


def test_duration_tracking(test_db):
    history = make_sth(test_db, duration_in_state=86400)
    assert history.duration_in_state == 86400


def test_stay_entity_type(test_db):
    history = make_sth(test_db, entity_type="stay", entity_id=99)
    assert history.entity_type == "stay"
    assert history.entity_id == 99


def test_with_notes(test_db):
    history = make_sth(test_db, notes="Manual override by manager")
    assert history.notes == "Manual override by manager"


def test_transitioned_at_is_set(test_db):
    history = make_sth(test_db)
    assert history.transitioned_at is not None


# ---------------------------------------------------------------------------
# set_context / get_context
# ---------------------------------------------------------------------------


def test_set_and_get_context(test_db):
    history = make_sth(test_db)
    history.set_context({"room": "101", "rate": 150})
    assert history.get_context() == {"room": "101", "rate": 150}


def test_set_context_persists_as_json_string(test_db):
    history = make_sth(test_db)
    history.set_context({"key": "value"})
    assert json.loads(history.context_data) == {"key": "value"}


def test_set_context_with_date_uses_str_default(test_db):
    from datetime import date

    history = make_sth(test_db)
    history.set_context({"check_in": date(2025, 6, 1)})
    result = history.get_context()
    assert "check_in" in result
    assert "2025-06-01" in result["check_in"]


def test_set_context_empty_dict(test_db):
    history = make_sth(test_db)
    history.set_context({})
    assert history.get_context() == {}


def test_set_context_nested(test_db):
    history = make_sth(test_db)
    data = {"guest": {"name": "John", "id": 5}, "nights": 3}
    history.set_context(data)
    assert history.get_context() == data


def test_get_context_none(test_db):
    history = make_sth(test_db, context_data=None)
    assert history.get_context() == {}


def test_get_context_invalid_json(test_db):
    history = make_sth(test_db, context_data="not valid {{json")
    assert history.get_context() == {}


def test_get_context_empty_string(test_db):
    history = make_sth(test_db, context_data="")
    assert history.get_context() == {}


# ---------------------------------------------------------------------------
# to_dict
# ---------------------------------------------------------------------------


def test_to_dict_basic(test_db):
    history = make_sth(
        test_db,
        entity_type="reservation",
        entity_id=42,
        from_state="pending",
        to_state="confirmed",
        transition_name="confirm",
        triggered_by="staff@hotel.com",
        trigger_type="manual",
        is_successful=True,
    )
    d = history.to_dict()
    assert d["entity_type"] == "reservation"
    assert d["entity_id"] == 42
    assert d["from_state"] == "pending"
    assert d["to_state"] == "confirmed"
    assert d["transition_name"] == "confirm"
    assert d["is_successful"] is True
    assert d["triggered_by"] == "staff@hotel.com"
    assert d["trigger_type"] == "manual"
    assert d["transitioned_at"] is not None


def test_to_dict_with_context(test_db):
    history = make_sth(test_db)
    history.set_context({"note": "VIP guest"})
    d = history.to_dict()
    assert d["context_data"] == {"note": "VIP guest"}


def test_to_dict_null_context(test_db):
    history = make_sth(test_db, context_data=None)
    d = history.to_dict()
    assert d["context_data"] == {}


def test_to_dict_with_error_info(test_db):
    history = make_sth(
        test_db,
        is_successful=False,
        error_message="Room not available",
        error_code="ROOM_UNAVAILABLE",
    )
    d = history.to_dict()
    assert d["is_successful"] is False
    assert d["error_message"] == "Room not available"
    assert d["error_code"] == "ROOM_UNAVAILABLE"


def test_to_dict_with_duration(test_db):
    history = make_sth(test_db, duration_in_state=3600)
    d = history.to_dict()
    assert d["duration_in_state"] == 3600


def test_to_dict_null_from_state(test_db):
    history = make_sth(test_db, from_state=None)
    d = history.to_dict()
    assert d["from_state"] is None


def test_to_dict_all_keys_present(test_db):
    history = make_sth(test_db)
    d = history.to_dict()
    expected_keys = {
        "id",
        "entity_type",
        "entity_id",
        "from_state",
        "to_state",
        "transition_name",
        "is_successful",
        "triggered_by",
        "trigger_type",
        "context_data",
        "notes",
        "error_message",
        "error_code",
        "transitioned_at",
        "duration_in_state",
    }
    assert expected_keys.issubset(set(d.keys()))


# ---------------------------------------------------------------------------
# __repr__
# ---------------------------------------------------------------------------


def test_repr(test_db):
    history = make_sth(
        test_db,
        entity_type="stay",
        entity_id=7,
        from_state="active",
        to_state="checked_out",
    )
    r = repr(history)
    assert "stay:7" in r
    assert "active" in r
    assert "checked_out" in r


def test_repr_null_from_state(test_db):
    history = make_sth(test_db, from_state=None, to_state="pending")
    r = repr(history)
    assert "None" in r
    assert "pending" in r
