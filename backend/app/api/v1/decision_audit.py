"""Decision Audit Ledger API — read-mostly, override + outcome write."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db, require_role
from app.models import User
from app.services.decision_audit_service import DecisionAuditService

router = APIRouter(prefix="/decision-audit", tags=["Decision Audit Ledger"])


def _serialize(e) -> dict:
    return {
        "id": e.id,
        "feature_id": e.feature_id,
        "decision_type": e.decision_type,
        "outcome": e.outcome,
        "inputs": e.inputs,
        "contributions": e.contributions,
        "model_version": e.model_version,
        "confidence": e.confidence,
        "resource_kind": e.resource_kind,
        "resource_id": e.resource_id,
        "correlation_id": e.correlation_id,
        "status": e.status.value if e.status else None,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }


def _serialize_override(o) -> dict:
    return {
        "id": o.id,
        "decision_entry_id": o.decision_entry_id,
        "original_outcome": o.original_outcome,
        "new_outcome": o.new_outcome,
        "reason": o.reason,
        "actor_user_id": o.actor_user_id,
        "created_at": o.created_at.isoformat() if o.created_at else None,
    }


def _serialize_outcome(o) -> dict:
    return {
        "id": o.id,
        "decision_entry_id": o.decision_entry_id,
        "outcome_label": o.outcome_label,
        "outcome_value": o.outcome_value,
        "observed_at": o.observed_at.isoformat() if o.observed_at else None,
        "notes": o.notes,
    }


class OverrideIn(BaseModel):
    new_outcome: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)


class OutcomeIn(BaseModel):
    outcome_label: str = Field(..., min_length=1)
    outcome_value: Optional[dict] = None
    notes: Optional[str] = None


@router.get("")
def list_entries(
    feature_id: Optional[str] = None,
    decision_type: Optional[str] = None,
    outcome: Optional[str] = None,
    resource_kind: Optional[str] = None,
    resource_id: Optional[str] = None,
    since_days: int = Query(30, ge=1, le=365),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows, total = DecisionAuditService(db).list_entries(
        feature_id=feature_id,
        decision_type=decision_type,
        outcome=outcome,
        resource_kind=resource_kind,
        resource_id=resource_id,
        since_days=since_days,
        limit=limit,
        offset=offset,
    )
    return {
        "items": [_serialize(r) for r in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{entry_id}")
def get_entry(
    entry_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    e = DecisionAuditService(db).get(entry_id)
    if not e:
        raise HTTPException(status_code=404, detail="Not found")
    return {
        **_serialize(e),
        "overrides": [
            _serialize_override(o)
            for o in DecisionAuditService(db).get_overrides(entry_id)
        ],
        "outcomes": [
            _serialize_outcome(o)
            for o in DecisionAuditService(db).get_outcomes(entry_id)
        ],
    }


@router.post("/{entry_id}/override")
def override_decision(
    entry_id: int,
    payload: OverrideIn,
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    o = DecisionAuditService(db).override(
        entry_id,
        new_outcome=payload.new_outcome,
        reason=payload.reason,
        actor_user_id=current_user.id,
    )
    if not o:
        raise HTTPException(status_code=404, detail="Not found")
    return _serialize_override(o)


@router.post("/{entry_id}/outcome")
def attach_outcome(
    entry_id: int,
    payload: OutcomeIn,
    _: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    o = DecisionAuditService(db).attach_outcome(
        entry_id,
        outcome_label=payload.outcome_label,
        outcome_value=payload.outcome_value,
        notes=payload.notes,
    )
    if not o:
        raise HTTPException(status_code=404, detail="Not found")
    return _serialize_outcome(o)


@router.get("/_/accuracy")
def accuracy(
    since_days: int = Query(60, ge=7, le=365),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {
        "rows": DecisionAuditService(db).accuracy_by_feature(since_days=since_days)
    }
