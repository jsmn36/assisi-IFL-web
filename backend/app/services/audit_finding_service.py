"""Service for the Audit Finding Tracker."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.audit_finding import (
    AuditFinding,
    AuditFindingActivity,
    FindingSeverity,
    FindingSource,
    FindingStatus,
)


class AuditFindingService:
    def __init__(self, db: Session):
        self.db = db

    # ---------- queries ----------

    def list(
        self,
        status: Optional[FindingStatus] = None,
        severity: Optional[FindingSeverity] = None,
        owner_user_id: Optional[int] = None,
        source: Optional[FindingSource] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[AuditFinding], int]:
        q = self.db.query(AuditFinding)
        if status:
            q = q.filter(AuditFinding.status == status)
        if severity:
            q = q.filter(AuditFinding.severity == severity)
        if owner_user_id is not None:
            q = q.filter(AuditFinding.owner_user_id == owner_user_id)
        if source:
            q = q.filter(AuditFinding.source == source)
        if search:
            term = f"%{search.lower()}%"
            q = q.filter(
                (AuditFinding.title.ilike(term))
                | (AuditFinding.reference.ilike(term))
            )
        total = q.count()
        rows = (
            q.order_by(AuditFinding.due_date.is_(None), AuditFinding.due_date.asc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return rows, total

    def get(self, finding_id: int) -> Optional[AuditFinding]:
        return (
            self.db.query(AuditFinding)
            .filter(AuditFinding.id == finding_id)
            .first()
        )

    # ---------- mutations ----------

    def _log(
        self,
        finding: AuditFinding,
        event_type: str,
        payload: dict,
        actor_user_id: Optional[int],
    ) -> None:
        self.db.add(
            AuditFindingActivity(
                finding_id=finding.id,
                actor_user_id=actor_user_id,
                event_type=event_type,
                payload=json.dumps(payload, default=str),
            )
        )

    def create(
        self,
        *,
        title: str,
        source: FindingSource = FindingSource.INTERNAL_AUDIT,
        severity: FindingSeverity = FindingSeverity.MEDIUM,
        description: Optional[str] = None,
        reference: Optional[str] = None,
        owner_user_id: Optional[int] = None,
        due_date: Optional[datetime] = None,
        created_by: Optional[int] = None,
    ) -> AuditFinding:
        finding = AuditFinding(
            title=title,
            description=description,
            reference=reference,
            source=source,
            severity=severity,
            owner_user_id=owner_user_id,
            due_date=due_date,
            created_by=created_by,
        )
        self.db.add(finding)
        self.db.flush()
        self._log(
            finding,
            "created",
            {"title": title, "severity": severity.value, "source": source.value},
            actor_user_id=created_by,
        )
        self.db.commit()
        self.db.refresh(finding)
        return finding

    def update_status(
        self,
        finding_id: int,
        status: FindingStatus,
        actor_user_id: Optional[int] = None,
        note: Optional[str] = None,
    ) -> Optional[AuditFinding]:
        finding = self.get(finding_id)
        if not finding:
            return None
        prev = finding.status
        finding.status = status
        if status == FindingStatus.CLOSED:
            finding.closed_at = datetime.now(timezone.utc)
            finding.closed_by = actor_user_id
        self._log(
            finding,
            "status_change",
            {"from": prev.value, "to": status.value, "note": note},
            actor_user_id=actor_user_id,
        )
        self.db.commit()
        self.db.refresh(finding)
        return finding

    def add_note(
        self,
        finding_id: int,
        note: str,
        actor_user_id: Optional[int] = None,
    ) -> Optional[AuditFinding]:
        finding = self.get(finding_id)
        if not finding:
            return None
        self._log(finding, "note", {"note": note}, actor_user_id=actor_user_id)
        self.db.commit()
        self.db.refresh(finding)
        return finding

    def assign(
        self,
        finding_id: int,
        owner_user_id: Optional[int],
        actor_user_id: Optional[int] = None,
    ) -> Optional[AuditFinding]:
        finding = self.get(finding_id)
        if not finding:
            return None
        prev = finding.owner_user_id
        finding.owner_user_id = owner_user_id
        self._log(
            finding,
            "assignment",
            {"from": prev, "to": owner_user_id},
            actor_user_id=actor_user_id,
        )
        self.db.commit()
        self.db.refresh(finding)
        return finding

    def close(
        self,
        finding_id: int,
        resolution_summary: str,
        evidence_url: Optional[str] = None,
        actor_user_id: Optional[int] = None,
    ) -> Optional[AuditFinding]:
        finding = self.get(finding_id)
        if not finding:
            return None
        finding.status = FindingStatus.CLOSED
        finding.closed_at = datetime.now(timezone.utc)
        finding.closed_by = actor_user_id
        finding.resolution_summary = resolution_summary
        finding.evidence_url = evidence_url
        self._log(
            finding,
            "closed",
            {"summary": resolution_summary, "evidence_url": evidence_url},
            actor_user_id=actor_user_id,
        )
        self.db.commit()
        self.db.refresh(finding)
        return finding

    def escalate(
        self,
        finding_id: int,
        escalated_to_user_id: int,
        actor_user_id: Optional[int] = None,
    ) -> Optional[AuditFinding]:
        finding = self.get(finding_id)
        if not finding:
            return None
        finding.status = FindingStatus.ESCALATED
        finding.escalated_at = datetime.now(timezone.utc)
        finding.escalated_to_user_id = escalated_to_user_id
        self._log(
            finding,
            "escalation",
            {"to": escalated_to_user_id},
            actor_user_id=actor_user_id,
        )
        self.db.commit()
        self.db.refresh(finding)
        return finding

    def sweep_overdue(self) -> int:
        """Flag open findings whose due dates have passed."""
        now = datetime.now(timezone.utc)
        rows = (
            self.db.query(AuditFinding)
            .filter(AuditFinding.due_date.isnot(None))
            .filter(AuditFinding.due_date < now)
            .filter(
                AuditFinding.status.in_(
                    [
                        FindingStatus.OPEN,
                        FindingStatus.IN_REMEDIATION,
                        FindingStatus.AWAITING_VERIFICATION,
                    ]
                )
            )
            .all()
        )
        for r in rows:
            r.status = FindingStatus.OVERDUE
            self._log(
                r,
                "auto_overdue",
                {"due_date": r.due_date.isoformat() if r.due_date else None},
                actor_user_id=None,
            )
        self.db.commit()
        return len(rows)
