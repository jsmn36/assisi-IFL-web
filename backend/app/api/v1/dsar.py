"""DSAR + Consent Version REST API."""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db, require_role
from app.models import User
from app.models.dsar import (
    ConsentKind,
    DSARKind,
    DSARStatus,
)
from app.services.dsar_service import ConsentService, DSARService

router = APIRouter(prefix="/dsar", tags=["DSAR & Consent"])


# ----- DSAR -----


def _serialize_request(r) -> dict:
    return {
        "id": r.id,
        "subject_email": r.subject_email,
        "subject_name": r.subject_name,
        "guest_id": r.guest_id,
        "kind": r.kind.value,
        "status": r.status.value,
        "summary": r.summary,
        "identity_verified_at": r.identity_verified_at.isoformat() if r.identity_verified_at else None,
        "identity_verified_by": r.identity_verified_by,
        "delivery_method": r.delivery_method,
        "delivered_at": r.delivered_at.isoformat() if r.delivered_at else None,
        "delivered_by": r.delivered_by,
        "delivered_file_path": r.delivered_file_path,
        "delivered_file_sha256": r.delivered_file_sha256,
        "notes": r.notes,
        "received_at": r.received_at.isoformat() if r.received_at else None,
        "due_date": r.due_date.isoformat() if r.due_date else None,
        "closed_at": r.closed_at.isoformat() if r.closed_at else None,
    }


class DSARIntakeIn(BaseModel):
    subject_email: str
    subject_name: Optional[str] = None
    kind: DSARKind
    summary: Optional[str] = None
    guest_id: Optional[int] = None


class DSARStatusIn(BaseModel):
    status: DSARStatus
    notes: Optional[str] = None


class DSARDeliverIn(BaseModel):
    delivery_method: str
    file_path: Optional[str] = None
    file_sha256: Optional[str] = None


@router.post("/requests", status_code=201)
def intake_request(
    payload: DSARIntakeIn,
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    r = DSARService(db).intake(
        subject_email=payload.subject_email,
        subject_name=payload.subject_name,
        kind=payload.kind,
        summary=payload.summary,
        guest_id=payload.guest_id,
        created_by=current_user.id,
    )
    return _serialize_request(r)


@router.get("/requests")
def list_requests(
    status: Optional[DSARStatus] = None,
    kind: Optional[DSARKind] = None,
    overdue_only: bool = False,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    _: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    rows, total = DSARService(db).list(
        status=status,
        kind=kind,
        overdue_only=overdue_only,
        limit=limit,
        offset=offset,
    )
    return {
        "items": [_serialize_request(r) for r in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("/requests/{request_id}/status")
def update_request_status(
    request_id: int,
    payload: DSARStatusIn,
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    r = DSARService(db).update_status(
        request_id, payload.status, actor_user_id=current_user.id, notes=payload.notes
    )
    if not r:
        raise HTTPException(status_code=404, detail="Not found")
    return _serialize_request(r)


@router.post("/requests/{request_id}/verify-identity")
def verify_identity(
    request_id: int,
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    r = DSARService(db).verify_identity(request_id, current_user.id)
    if not r:
        raise HTTPException(status_code=404, detail="Not found")
    return _serialize_request(r)


@router.post("/requests/{request_id}/deliver")
def mark_delivered(
    request_id: int,
    payload: DSARDeliverIn,
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    r = DSARService(db).mark_delivered(
        request_id,
        delivery_method=payload.delivery_method,
        file_path=payload.file_path,
        file_sha256=payload.file_sha256,
        actor_user_id=current_user.id,
    )
    if not r:
        raise HTTPException(status_code=404, detail="Not found")
    return _serialize_request(r)


# ----- Consent -----


def _serialize_version(v) -> dict:
    return {
        "id": v.id,
        "kind": v.kind.value,
        "version_label": v.version_label,
        "body": v.body,
        "body_sha256": v.body_sha256,
        "effective_at": v.effective_at.isoformat() if v.effective_at else None,
        "deprecated_at": v.deprecated_at.isoformat() if v.deprecated_at else None,
        "created_by": v.created_by,
        "created_at": v.created_at.isoformat() if v.created_at else None,
    }


class ConsentVersionIn(BaseModel):
    kind: ConsentKind
    version_label: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)
    effective_at: Optional[datetime] = None


class ConsentAcceptIn(BaseModel):
    consent_version_id: int
    guest_id: Optional[int] = None
    subject_email: Optional[str] = None
    accepted: bool = True
    method: Optional[str] = None


@router.get("/consent/versions")
def list_consent_versions(
    kind: Optional[ConsentKind] = None,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = ConsentService(db).list_versions(kind=kind)
    return {"items": [_serialize_version(v) for v in rows]}


@router.post("/consent/versions", status_code=201)
def publish_consent_version(
    payload: ConsentVersionIn,
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    v = ConsentService(db).publish_version(
        kind=payload.kind,
        version_label=payload.version_label,
        body=payload.body,
        effective_at=payload.effective_at,
        created_by=current_user.id,
    )
    return _serialize_version(v)


@router.get("/consent/latest/{kind}")
def get_latest_version(
    kind: ConsentKind,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    v = ConsentService(db).latest_version(kind)
    if not v:
        raise HTTPException(status_code=404, detail="No active version")
    return _serialize_version(v)


@router.post("/consent/records", status_code=201)
def record_consent(
    payload: ConsentAcceptIn,
    request: Request,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    r = ConsentService(db).record_acceptance(
        consent_version_id=payload.consent_version_id,
        guest_id=payload.guest_id,
        subject_email=payload.subject_email,
        accepted=payload.accepted,
        method=payload.method,
        ip_address=ip,
        user_agent=ua,
    )
    return {
        "id": r.id,
        "consent_version_id": r.consent_version_id,
        "guest_id": r.guest_id,
        "accepted": r.accepted,
        "captured_at": r.captured_at.isoformat() if r.captured_at else None,
    }


@router.get("/consent/records/guest/{guest_id}")
def consent_history_for_guest(
    guest_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = ConsentService(db).history_for_guest(guest_id)
    return {
        "items": [
            {
                "record_id": rec.id,
                "consent_version_id": ver.id,
                "kind": ver.kind.value,
                "version_label": ver.version_label,
                "accepted": rec.accepted,
                "method": rec.method,
                "captured_at": rec.captured_at.isoformat() if rec.captured_at else None,
            }
            for rec, ver in rows
        ]
    }
