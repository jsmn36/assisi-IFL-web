"""Ghost Booking Classifier REST API."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db, require_role
from app.models import User
from app.models.ghost_booking import GhostDecision, GhostRiskTier
from app.services.ghost_booking_service import (
    GBCInput,
    GhostBookingService,
)

router = APIRouter(prefix="/ghost-booking", tags=["Ghost Booking Classifier"])


def _serialize(row) -> dict:
    return {
        "id": row.id,
        "reservation_id": row.reservation_id,
        "guest_id": row.guest_id,
        "risk_score": row.risk_score,
        "risk_tier": row.risk_tier.value,
        "decision": row.decision.value,
        "signals_snapshot": row.signals_snapshot,
        "contributions": row.contributions,
        "overridden_at": row.overridden_at.isoformat() if row.overridden_at else None,
        "overridden_by": row.overridden_by,
        "override_reason": row.override_reason,
        "override_decision": row.override_decision.value if row.override_decision else None,
        "notes": row.notes,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


class ScoreReservationIn(BaseModel):
    reservation_id: int
    ip_country: Optional[str] = None
    billing_country: Optional[str] = None


class EvaluateIn(BaseModel):
    reservation_id: Optional[int] = None
    guest_id: Optional[int] = None
    guest_email: Optional[str] = None
    source: Optional[str] = None
    total_amount: float = 0
    number_of_nights: int = 0
    lead_time_hours: float = 0
    deposit_paid: float = 0
    ip_country: Optional[str] = None
    billing_country: Optional[str] = None
    is_group: bool = False


class OverrideIn(BaseModel):
    new_decision: GhostDecision
    reason: str = Field(..., min_length=1)


@router.post("/score", status_code=201)
def score_reservation(
    payload: ScoreReservationIn,
    _: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    try:
        row = GhostBookingService(db).score_reservation(
            reservation_id=payload.reservation_id,
            ip_country=payload.ip_country,
            billing_country=payload.billing_country,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _serialize(row)


@router.post("/evaluate")
def evaluate_inline(
    payload: EvaluateIn,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Score a hypothetical booking without writing — for booking-form gating."""
    from app.models import ReservationSource as _RS
    src = None
    if payload.source:
        try:
            src = _RS(payload.source)
        except ValueError:
            src = None
    gbc_input = GBCInput(
        reservation_id=payload.reservation_id,
        guest_id=payload.guest_id,
        guest_email=payload.guest_email,
        source=src,
        total_amount=payload.total_amount,
        number_of_nights=payload.number_of_nights,
        lead_time_hours=payload.lead_time_hours,
        deposit_paid=payload.deposit_paid,
        ip_country=payload.ip_country,
        billing_country=payload.billing_country,
        is_group=payload.is_group,
    )
    score, tier, decision, contributions = GhostBookingService(db).evaluate_only(gbc_input)
    return {
        "risk_score": score,
        "risk_tier": tier.value,
        "decision": decision.value,
        "contributions": [
            {"signal": c.signal, "points": c.points, "evidence": c.evidence}
            for c in contributions
        ],
    }


@router.get("")
def list_scores(
    tier: Optional[GhostRiskTier] = None,
    decision: Optional[GhostDecision] = None,
    since_days: int = Query(30, ge=1, le=365),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows, total = GhostBookingService(db).list_scores(
        tier=tier, decision=decision, since_days=since_days, limit=limit, offset=offset
    )
    return {
        "items": [_serialize(r) for r in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{score_id}")
def get_score(
    score_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = GhostBookingService(db).get(score_id)
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    return _serialize(row)


@router.post("/{score_id}/override")
def override(
    score_id: int,
    payload: OverrideIn,
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    row = GhostBookingService(db).override(
        score_id,
        payload.new_decision,
        actor_user_id=current_user.id,
        reason=payload.reason,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    return _serialize(row)
