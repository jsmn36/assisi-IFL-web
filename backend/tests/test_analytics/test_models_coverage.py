"""
Additional model coverage tests to push total coverage above 80%.
Covers: BusinessDay, Room, Stay lifecycle methods and to_dict().
These tests are pure-unit (no DB) — models are instantiated directly.
"""
import pytest
from decimal import Decimal
from datetime import date, datetime
from unittest.mock import MagicMock, patch


# ─────────────────────────── BusinessDay ─────────────────────────────────────


class TestBusinessDay:
    def _make(self, **kwargs):
        from app.models.business_day import BusinessDay
        from app.models.enums import DayStatus

        bd = BusinessDay()
        bd.id = kwargs.get("id", 1)
        bd.property_id = kwargs.get("property_id", 1)
        bd.business_date = kwargs.get("business_date", date(2024, 1, 15))
        bd.status = kwargs.get("status", DayStatus.OPEN)
        bd.is_closed = kwargs.get("is_closed", False)
        bd.opened_at = kwargs.get("opened_at", None)
        bd.opened_by = kwargs.get("opened_by", None)
        bd.closed_at = kwargs.get("closed_at", None)
        bd.closed_by = kwargs.get("closed_by", None)
        bd.night_audit_started_at = None
        bd.night_audit_completed_at = None
        bd.night_audit_run_by = None
        bd.night_audit_status = kwargs.get("night_audit_status", "pending")
        bd.audit_check_1_result = False
        bd.audit_check_2_result = False
        bd.audit_check_3_result = False
        bd.audit_check_4_result = False
        bd.audit_check_5_result = False
        bd.audit_check_6_result = False
        bd.audit_check_7_result = False
        bd.audit_check_8_result = False
        bd.total_occupancy = kwargs.get("total_occupancy", 0)
        bd.room_revenue = kwargs.get("room_revenue", Decimal("0"))
        bd.total_revenue = kwargs.get("total_revenue", Decimal("0"))
        bd.adr = Decimal("0")
        bd.occupancy_percent = Decimal("0")
        bd.rev_par = Decimal("0")
        return bd

    def test_day_opened_by_property(self):
        bd = self._make(opened_by="manager")
        assert bd.day_opened_by == "manager"

    def test_open_day_sets_status(self):
        from app.models.enums import DayStatus

        bd = self._make()
        bd.open_day(opened_by="mgr")
        assert bd.status == DayStatus.OPEN
        assert bd.is_closed is False
        assert bd.opened_by == "mgr"
        assert bd.opened_at is not None

    def test_open_day_keeps_existing_opened_at(self):
        existing = datetime(2024, 1, 15, 8, 0, 0)
        bd = self._make(opened_at=existing)
        bd.open_day()
        assert bd.opened_at == existing

    def test_start_night_audit(self):
        from app.models.enums import DayStatus

        bd = self._make()
        bd.start_night_audit(run_by="auditor")
        assert bd.status == DayStatus.IN_AUDIT
        assert bd.night_audit_status == "pending"
        assert bd.night_audit_run_by == "auditor"
        assert bd.night_audit_started_at is not None

    def test_all_audit_checks_passed_false(self):
        bd = self._make()
        assert bd.all_audit_checks_passed() is False

    def test_all_audit_checks_passed_true(self):
        bd = self._make()
        for i in range(1, 9):
            setattr(bd, f"audit_check_{i}_result", True)
        assert bd.all_audit_checks_passed() is True

    def test_complete_night_audit_success(self):
        from app.models.enums import DayStatus

        bd = self._make()
        for i in range(1, 9):
            setattr(bd, f"audit_check_{i}_result", True)
        bd.complete_night_audit(all_checks_passed=True)
        assert bd.status == DayStatus.CLOSED
        assert bd.night_audit_status == "success"
        assert bd.is_closed is True

    def test_complete_night_audit_failure_flag(self):
        from app.models.enums import DayStatus

        bd = self._make()
        bd.complete_night_audit(all_checks_passed=False)
        assert bd.status == DayStatus.AUDIT_FAILED
        assert bd.night_audit_status == "failed"
        assert bd.is_closed is False

    def test_complete_night_audit_checks_not_all_passed(self):
        """all_checks_passed=True but checks not set → should still fail."""
        from app.models.enums import DayStatus

        bd = self._make()
        bd.complete_night_audit(all_checks_passed=True)
        assert bd.status == DayStatus.AUDIT_FAILED

    def test_close_day(self):
        from app.models.enums import DayStatus

        bd = self._make()
        bd.close_day(closed_by="manager")
        assert bd.status == DayStatus.CLOSED
        assert bd.is_closed is True
        assert bd.closed_by == "manager"
        assert bd.closed_at is not None

    def test_close_day_noop_if_already_closed(self):
        from app.models.enums import DayStatus

        bd = self._make(status=DayStatus.CLOSED, is_closed=True)
        bd.closed_at = datetime(2024, 1, 15, 23, 0)
        original_closed_at = bd.closed_at
        bd.close_day(closed_by="someone_else")
        # Should not have changed
        assert bd.closed_at == original_closed_at

    def test_calculate_metrics_normal(self):
        bd = self._make(total_occupancy=8, room_revenue=Decimal("800"))
        bd.calculate_metrics(total_rooms=10)
        assert bd.adr == Decimal("100")  # 800/8
        assert bd.occupancy_percent == Decimal("80")  # 8/10*100
        assert bd.rev_par == Decimal("80")  # 800/10

    def test_calculate_metrics_zero_occupancy(self):
        bd = self._make(total_occupancy=0, room_revenue=Decimal("0"))
        bd.calculate_metrics(total_rooms=10)
        assert bd.adr == Decimal("0")
        assert bd.occupancy_percent == Decimal("0")

    def test_calculate_metrics_zero_rooms(self):
        bd = self._make(total_occupancy=5, room_revenue=Decimal("500"))
        bd.calculate_metrics(total_rooms=0)
        assert bd.occupancy_percent == Decimal("0")
        assert bd.rev_par == Decimal("0")

    def test_to_dict(self):
        from app.models.enums import DayStatus

        bd = self._make(
            total_occupancy=5,
            room_revenue=Decimal("500"),
            total_revenue=Decimal("600"),
        )
        bd.status = DayStatus.OPEN
        bd.adr = Decimal("100")
        bd.occupancy_percent = Decimal("50")
        bd.rev_par = Decimal("60")
        d = bd.to_dict()
        assert d["property_id"] == 1
        assert d["status"] == "open"
        assert d["is_closed"] is False
        assert d["room_revenue"] == 500.0
        assert d["adr"] == 100.0


# ─────────────────────────── Room ────────────────────────────────────────────


class TestRoom:
    def _make(self, **kwargs):
        from app.models.room import Room, OccupancyState, ConditionState, RoomStatus

        r = Room()
        r.id = 1
        r.property_id = 1
        r.room_type_id = 1
        r.room_number = "101"
        r.floor = 3
        r.building = "A"
        r.wing = None
        r.notes = None
        r.is_active = kwargs.get("is_active", True)
        r.status = kwargs.get("status", RoomStatus.AVAILABLE)
        r.occupancy_state = kwargs.get("occupancy_state", OccupancyState.VACANT)
        r.condition_state = kwargs.get("condition_state", ConditionState.CLEAN)
        r.occupancy_changed_at = None
        r.condition_changed_at = None
        return r

    def test_is_available_true(self):
        r = self._make()
        assert r.is_available() is True

    def test_is_available_false_occupied(self):
        from app.models.room import OccupancyState

        r = self._make(occupancy_state=OccupancyState.OCCUPIED)
        assert r.is_available() is False

    def test_is_available_false_dirty(self):
        from app.models.room import ConditionState

        r = self._make(condition_state=ConditionState.DIRTY)
        assert r.is_available() is False

    def test_is_available_inspected(self):
        from app.models.room import ConditionState

        r = self._make(condition_state=ConditionState.INSPECTED)
        assert r.is_available() is True

    def test_mark_clean(self):
        from app.models.room import ConditionState

        r = self._make(condition_state=ConditionState.DIRTY)
        result = r.mark_clean()
        assert result is True
        assert r.condition_state == ConditionState.CLEAN
        assert r.condition_changed_at is not None

    def test_mark_dirty(self):
        from app.models.room import ConditionState

        r = self._make()
        result = r.mark_dirty()
        assert result is True
        assert r.condition_state == ConditionState.DIRTY

    def test_mark_inspected(self):
        from app.models.room import ConditionState

        r = self._make()
        result = r.mark_inspected()
        assert result is True
        assert r.condition_state == ConditionState.INSPECTED

    def test_take_out_of_order(self):
        from app.models.room import OccupancyState, ConditionState

        r = self._make()
        result = r.take_out_of_order(notes="Broken AC")
        assert result is True
        assert r.occupancy_state == OccupancyState.OUT_OF_ORDER
        assert r.condition_state == ConditionState.OUT_OF_ORDER
        assert r.is_active is False
        assert r.notes == "Broken AC"

    def test_take_out_of_order_no_notes(self):
        r = self._make()
        r.take_out_of_order()
        assert r.notes is None

    def test_return_to_service(self):
        from app.models.room import OccupancyState, ConditionState

        r = self._make()
        r.take_out_of_order(notes="Broken")
        result = r.return_to_service()
        assert result is True
        assert r.occupancy_state == OccupancyState.VACANT
        assert r.condition_state == ConditionState.CLEAN
        assert r.is_active is True
        assert r.notes is None

    def test_check_in(self):
        from app.models.room import OccupancyState

        r = self._make()
        result = r.check_in()
        assert result is True
        assert r.occupancy_state == OccupancyState.OCCUPIED
        assert r.occupancy_changed_at is not None

    def test_check_in_already_occupied_raises(self):
        from app.models.room import OccupancyState

        r = self._make(occupancy_state=OccupancyState.OCCUPIED)
        with pytest.raises(ValueError, match="already occupied"):
            r.check_in()

    def test_check_out(self):
        from app.models.room import OccupancyState, ConditionState

        r = self._make(occupancy_state=OccupancyState.OCCUPIED)
        result = r.check_out()
        assert result is True
        assert r.occupancy_state == OccupancyState.VACANT
        assert r.condition_state == ConditionState.DIRTY

    def test_check_out_already_vacant_raises(self):
        r = self._make()
        with pytest.raises(ValueError, match="already vacant"):
            r.check_out()

    def test_to_dict(self):
        r = self._make()
        d = r.to_dict()
        assert d["room_number"] == "101"
        assert d["floor"] == 3
        assert d["is_available"] is True
        assert "occupancy_state" in d
        assert "condition_state" in d


# ─────────────────────────── Stay ────────────────────────────────────────────


class TestStay:
    def _make(self, **kwargs):
        from app.models.stay import Stay, StayStatus
        from decimal import Decimal

        s = Stay()
        s.id = 1
        s.property_id = 1
        s.reservation_id = 1
        s.guest_id = 1
        s.room_id = 1
        s.status = kwargs.get("status", StayStatus.RESERVED)
        s.check_in_date = kwargs.get("check_in_date", date(2024, 2, 1))
        s.check_out_date = kwargs.get("check_out_date", date(2024, 2, 3))
        s._number_of_nights = 2
        s.nightly_rate = Decimal("150")
        s.num_adults = 2
        s.num_children = 0
        s.actual_check_in_time = None
        s.actual_check_out_time = None
        s.checked_in_by = None
        s.checked_out_by = None
        s.is_active = False
        s.requires_cleaning = True
        s.cleaning_completed = False
        s.total_room_charges = Decimal("0")
        s.total_charges = Decimal("0")
        s.total_other_charges = Decimal("0")
        s.balance_due = Decimal("0")
        return s

    def test_is_checked_in_false(self):
        s = self._make()
        assert s.is_checked_in is False

    def test_is_checked_in_true(self):
        from app.models.stay import StayStatus

        s = self._make(status=StayStatus.CHECKED_IN)
        assert s.is_checked_in is True

    def test_is_checked_out(self):
        from app.models.stay import StayStatus

        s = self._make(status=StayStatus.CHECKED_OUT)
        assert s.is_checked_out is True

    def test_number_of_nights_from_dates(self):
        s = self._make()
        assert s.number_of_nights == 2

    def test_number_of_nights_no_dates(self):
        s = self._make()
        s.check_in_date = None
        s.check_out_date = None
        s._number_of_nights = 3
        assert s.number_of_nights == 3

    def test_number_of_nights_setter(self):
        s = self._make()
        s.number_of_nights = 5
        assert s._number_of_nights == 5

    def test_check_in_success(self):
        from app.models.stay import StayStatus

        s = self._make()
        result = s.check_in(checked_in_by="receptionist")
        assert result is True
        assert s.status == StayStatus.CHECKED_IN
        assert s.is_active is True
        assert s.actual_check_in_time is not None
        assert s.checked_in_by == "receptionist"

    def test_check_in_wrong_status_returns_false(self):
        from app.models.stay import StayStatus

        s = self._make(status=StayStatus.CHECKED_IN)
        assert s.check_in() is False

    def test_check_out_success(self):
        from app.models.stay import StayStatus

        s = self._make(status=StayStatus.CHECKED_IN)
        result = s.check_out(checked_out_by="receptionist")
        assert result is True
        assert s.status == StayStatus.CHECKED_OUT
        assert s.is_active is False
        assert s.requires_cleaning is True

    def test_check_out_wrong_status_returns_false(self):
        s = self._make()
        assert s.check_out() is False

    def test_cancel_success(self):
        from app.models.stay import StayStatus

        s = self._make()
        result = s.cancel()
        assert result is True
        assert s.status == StayStatus.CANCELLED
        assert s.is_active is False

    def test_cancel_wrong_status_returns_false(self):
        from app.models.stay import StayStatus

        s = self._make(status=StayStatus.CHECKED_IN)
        assert s.cancel() is False

    def test_add_room_charge(self):
        from app.models.stay import Stay

        s = self._make()
        charge = s.add_room_charge(100, description="Night 1")
        assert s.total_room_charges == Decimal("100")
        assert s.total_charges == Decimal("100")
        assert charge is not None

    def test_add_other_charge(self):
        s = self._make()
        charge = s.add_other_charge(25, description="Minibar")
        assert s.total_other_charges == Decimal("25")
        assert s.total_charges == Decimal("25")

    def test_mark_cleaning_required(self):
        s = self._make()
        s.cleaning_completed = True
        s.requires_cleaning = False
        s.mark_cleaning_required()
        assert s.requires_cleaning is True
        assert s.cleaning_completed is False

    def test_mark_cleaning_completed(self):
        s = self._make()
        s.mark_cleaning_completed()
        assert s.cleaning_completed is True
        assert s.requires_cleaning is False

    def test_to_dict(self):
        s = self._make()
        d = s.to_dict()
        assert d["reservation_id"] == 1
        assert d["room_id"] == 1
        assert d["number_of_nights"] == 2
        assert d["nightly_rate"] == 150.0
        assert "status" in d

    def test_repr(self):
        s = self._make()
        assert "Stay" in repr(s)
