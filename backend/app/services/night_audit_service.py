import logging
from datetime import date
from sqlalchemy.orm import Session

from app.services.base_service import BaseService
from app.models.business_day import BusinessDay
from app.models.enums import DayStatus
from app.gates.base import GateError
from app.gates.coordinator import TransactionCoordinator
from app.gates.night_audit import NightAuditGate
from app.gates.night_audit_remediation import (
    NightAuditAutoExtendGate,
    NightAuditNoShowAndMetricsGate,
    NightAuditStartGate,
)

logger = logging.getLogger(__name__)


class NightAuditService(BaseService):
    """Orchestrates night audit via TransactionCoordinator (gate sequence, single commit)."""

    def __init__(self, db: Session):
        super().__init__(db)
        self._coordinator = TransactionCoordinator()

    def run_night_audit(
        self,
        property_id: int,
        audit_date: date | None = None,
        run_by: str = "system",
        user_id: int | None = None,
        manual_override_justification: str | None = None,
        manual_override_target: str | None = None,
    ) -> dict:
        audit_date = audit_date or date.today()

        bd = (
            self.db.query(BusinessDay)
            .filter(
                BusinessDay.property_id == property_id,
                BusinessDay.business_date == audit_date,
            )
            .first()
        )

        if not bd:
            bd = BusinessDay(
                property_id=property_id,
                business_date=audit_date,
                status=DayStatus.OPEN,
            )
            self.db.add(bd)
            self.db.flush()

        if bd.night_audit_completed or bd.night_audit_status == "success":
            return {
                "status": "completed",
                "date": str(audit_date),
                "message": "Audit already successfully completed",
            }

        if bd.status in (DayStatus.CLOSED,):
            return {
                "status": "skipped",
                "date": str(audit_date),
                "message": "Business day already closed",
            }

        base_payload = {
            "property_id": property_id,
            "business_date": audit_date.isoformat(),
            "run_by": run_by,
        }

        gates = [
            (NightAuditStartGate(), base_payload),
            (NightAuditAutoExtendGate(), base_payload),
            (NightAuditNoShowAndMetricsGate(), base_payload),
            (NightAuditGate(), base_payload),
        ]

        try:
            combined = self._coordinator.run_sequence(gates, self.db, user_id=user_id)
            return {
                "status": "success",
                "date": str(audit_date),
                "gate_data": combined,
            }
        except GateError as exc:
            logger.warning("Night audit failed: %s", exc)
            return {
                "status": "failed",
                "date": str(audit_date),
                "error": str(exc),
            }

    def generate_audit_report(
        self, property_id: int, start_date: date, end_date: date
    ) -> dict:
        return {
            "property_id": property_id,
            "start": str(start_date),
            "end": str(end_date),
            "summary": "Audit Generated",
        }
