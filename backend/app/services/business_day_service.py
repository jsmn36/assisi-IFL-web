from datetime import date

from sqlalchemy.orm import Session

from app.services.base_service import BaseService, BusinessRuleError
from app.models.business_day import BusinessDay
from app.models.enums import DayStatus
from app.gates.base import GateError
from app.gates.coordinator import TransactionCoordinator
from app.gates.day_close import DayCloseGate
from app.gates.night_audit_remediation import NightAuditStartGate


class BusinessDayService(BaseService):
    def __init__(self, db: Session):
        super().__init__(db)
        self._coordinator = TransactionCoordinator()

    @staticmethod
    def _gate_user_id(user_id: int | str | None) -> int | None:
        """Normalize actor id to ``int`` for ``GateContext.user_id`` (``DayCloseGate`` stores ``str(user_id)``)."""
        if user_id is None:
            return None
        if isinstance(user_id, int):
            return user_id
        try:
            return int(str(user_id))
        except (TypeError, ValueError):
            return None

    def start_night_audit(
        self,
        property_id: int,
        business_date: date | None = None,
        run_by: str = "system",
        user_id: int | str | None = None,
    ) -> dict:
        """Set business day to IN_AUDIT via ``NightAuditStartGate`` (single gate, atomic commit)."""
        if business_date is None:
            business_date = self.get_active_business_day(property_id).business_date

        uid = self._gate_user_id(user_id)
        if run_by == "system" and uid is not None:
            run_by = str(uid)

        payload: dict = {
            "property_id": property_id,
            "business_date": business_date.isoformat(),
            "run_by": run_by,
        }
        try:
            return {
                "status": "success",
                "data": self._coordinator.run_sequence(
                    [(NightAuditStartGate(), payload)],
                    self.db,
                    user_id=uid,
                ),
            }
        except GateError as exc:
            raise BusinessRuleError(self._gate_error_message(exc)) from exc

    @staticmethod
    def _gate_error_message(exc: GateError) -> str:
        errs = getattr(exc, "errors", None) or []
        if errs:
            return "; ".join(errs)
        return str(exc)

    def _business_day_ready_for_close(self, property_id: int) -> BusinessDay | None:
        """
        Return the business day row that should be finalized: CLOSING with a completed night audit.

        Prefers the same row ``get_active_business_day`` would surface when it is already CLOSING
        (deterministic: latest ``business_date`` among active workflow statuses).
        """
        active = (
            self.db.query(BusinessDay)
            .filter(
                BusinessDay.property_id == property_id,
                BusinessDay.status.in_(
                    (DayStatus.OPEN, DayStatus.IN_AUDIT, DayStatus.CLOSING)
                ),
            )
            .order_by(BusinessDay.business_date.desc())
            .first()
        )
        if (
            active
            and active.status == DayStatus.CLOSING
            and active.night_audit_completed
        ):
            return active

        return (
            self.db.query(BusinessDay)
            .filter(
                BusinessDay.property_id == property_id,
                BusinessDay.status == DayStatus.CLOSING,
            )
            .order_by(BusinessDay.business_date.desc())
            .first()
        )

    def close_business_day(
        self, property_id: int, user_id: int | str | None = None
    ) -> dict:
        """
        Close the business day in CLOSING state using ``DayCloseGate``
        (after ``NightAuditGate`` has completed). Uses ``GateContext`` via ``TransactionCoordinator``.
        """
        bd = self._business_day_ready_for_close(property_id)

        if not bd:
            raise BusinessRuleError(
                "No business day in CLOSING state; complete night audit first"
            )

        if not bd.night_audit_completed:
            raise BusinessRuleError("Cannot close day. Night audit not successful")

        payload: dict = {
            "property_id": property_id,
            "business_date": bd.business_date.isoformat(),
        }
        uid = self._gate_user_id(user_id)

        try:
            data = self._coordinator.run_sequence(
                [(DayCloseGate(), payload)], self.db, user_id=uid
            )
            return {"status": "success", "data": data}
        except GateError as exc:
            raise BusinessRuleError(self._gate_error_message(exc)) from exc

    def get_active_business_day(self, property_id: int) -> BusinessDay:
        today = date.today()
        bd = (
            self.db.query(BusinessDay)
            .filter(
                BusinessDay.property_id == property_id,
                BusinessDay.status.in_(
                    [DayStatus.OPEN, DayStatus.IN_AUDIT, DayStatus.CLOSING]
                ),
            )
            .order_by(BusinessDay.business_date.desc())
            .first()
        )

        if not bd:
            bd = BusinessDay(
                property_id=property_id,
                business_date=today,
                status=DayStatus.OPEN,
            )
            self.db.add(bd)
            self.db.commit()

        return bd
