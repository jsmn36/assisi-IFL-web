"""Audit Finding Tracker REST API."""
import json
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db, require_role
from app.models import User
from app.models.audit_finding import (
    AuditFinding,
    FindingSeverity,
    FindingSource,
    FindingStatus,
)
from app.services.audit_finding_service import AuditFindingService

router = APIRouter(prefix="/audit-findings", tags=["Audit Findings"])


def _serialize(f: AuditFinding, *, with_activity: bool = False) -> dict:
    out = {
        "id": f.id,
        "reference": f.reference,
        "title": f.title,
        "description": f.description,
        "source": f.source.value if f.source else None,
        "severity": f.severity.value if f.severity else None,
        "status": f.status.value if f.status else None,
        "owner_user_id": f.owner_user_id,
        "due_date": f.due_date.isoformat() if f.due_date else None,
        "escalated_at": f.escalated_at.isoformat() if f.escalated_at else None,
        "escalated_to_user_id": f.escalated_to_user_id,
        "closed_at": f.closed_at.isoformat() if f.closed_at else None,
        "closed_by": f.closed_by,
        "resolution_summary": f.resolution_summary,
        "evidence_url": f.evidence_url,
        "created_at": f.created_at.isoformat() if f.created_at else None,
    }
    if with_activity:
        out["activity"] = [
            {
                "id": a.id,
                "actor_user_id": a.actor_user_id,
                "event_type": a.event_type,
                "payload": _safe_load(a.payload),
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in (f.activity or [])
        ]
    return out


def _safe_load(text: Optional[str]):
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


class FindingCreate(BaseModel):
    title: str = Field(..., min_length=2)
    description: Optional[str] = None
    reference: Optional[str] = None
    source: FindingSource = FindingSource.INTERNAL_AUDIT
    severity: FindingSeverity = FindingSeverity.MEDIUM
    owner_user_id: Optional[int] = None
    due_date: Optional[datetime] = None


class StatusChange(BaseModel):
    status: FindingStatus
    note: Optional[str] = None


class NoteIn(BaseModel):
    note: str = Field(..., min_length=1)


class AssignIn(BaseModel):
    owner_user_id: Optional[int] = None


class CloseIn(BaseModel):
    resolution_summary: str = Field(..., min_length=1)
    evidence_url: Optional[str] = None


class EscalateIn(BaseModel):
    escalated_to_user_id: int


@router.get("")
def list_findings(
    status: Optional[FindingStatus] = None,
    severity: Optional[FindingSeverity] = None,
    owner_user_id: Optional[int] = None,
    source: Optional[FindingSource] = None,
    search: Optional[str] = Query(None, min_length=1),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows, total = AuditFindingService(db).list(
        status=status,
        severity=severity,
        owner_user_id=owner_user_id,
        source=source,
        search=search,
        limit=limit,
        offset=offset,
    )
    return {
        "items": [_serialize(r) for r in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("", status_code=201)
def create_finding(
    payload: FindingCreate,
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    f = AuditFindingService(db).create(
        title=payload.title,
        description=payload.description,
        reference=payload.reference,
        source=payload.source,
        severity=payload.severity,
        owner_user_id=payload.owner_user_id,
        due_date=payload.due_date,
        created_by=current_user.id,
    )
    return _serialize(f, with_activity=True)


@router.get("/{finding_id}")
def get_finding(
    finding_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    f = AuditFindingService(db).get(finding_id)
    if not f:
        raise HTTPException(status_code=404, detail="Not found")
    return _serialize(f, with_activity=True)


@router.post("/{finding_id}/status")
def change_status(
    finding_id: int,
    payload: StatusChange,
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    f = AuditFindingService(db).update_status(
        finding_id, payload.status, actor_user_id=current_user.id, note=payload.note
    )
    if not f:
        raise HTTPException(status_code=404, detail="Not found")
    return _serialize(f, with_activity=True)


@router.post("/{finding_id}/notes")
def add_note(
    finding_id: int,
    payload: NoteIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    f = AuditFindingService(db).add_note(
        finding_id, payload.note, actor_user_id=current_user.id
    )
    if not f:
        raise HTTPException(status_code=404, detail="Not found")
    return _serialize(f, with_activity=True)


@router.post("/{finding_id}/assign")
def assign(
    finding_id: int,
    payload: AssignIn,
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    f = AuditFindingService(db).assign(
        finding_id,
        payload.owner_user_id,
        actor_user_id=current_user.id,
    )
    if not f:
        raise HTTPException(status_code=404, detail="Not found")
    return _serialize(f, with_activity=True)


@router.post("/{finding_id}/close")
def close(
    finding_id: int,
    payload: CloseIn,
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    f = AuditFindingService(db).close(
        finding_id,
        resolution_summary=payload.resolution_summary,
        evidence_url=payload.evidence_url,
        actor_user_id=current_user.id,
    )
    if not f:
        raise HTTPException(status_code=404, detail="Not found")
    return _serialize(f, with_activity=True)


@router.post("/{finding_id}/escalate")
def escalate(
    finding_id: int,
    payload: EscalateIn,
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    f = AuditFindingService(db).escalate(
        finding_id,
        escalated_to_user_id=payload.escalated_to_user_id,
        actor_user_id=current_user.id,
    )
    if not f:
        raise HTTPException(status_code=404, detail="Not found")
    return _serialize(f, with_activity=True)


@router.post("/sweep-overdue")
def sweep_overdue(
    _: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    n = AuditFindingService(db).sweep_overdue()
    return {"flagged_overdue": n}
