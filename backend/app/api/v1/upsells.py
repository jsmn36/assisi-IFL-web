"""Upsell chain CRUD + run controls."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db, require_role
from app.models import User
from app.models.upsell import UpsellStepType, UpsellTrigger
from app.services.upsell_service import UpsellService

router = APIRouter(prefix="/upsells", tags=["Upsell Chains"])


class UpsellStepIn(BaseModel):
    step_order: int
    step_type: UpsellStepType
    delay_minutes: int = 0
    subject: Optional[str] = None
    body_template: str


class UpsellChainCreate(BaseModel):
    name: str
    description: Optional[str] = None
    trigger: UpsellTrigger
    conditions: Optional[dict] = None
    steps: List[UpsellStepIn] = []


class UpsellChainUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    conditions: Optional[dict] = None
    is_active: Optional[bool] = None


def _serialize_chain(c) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "description": c.description,
        "trigger": c.trigger.value,
        "is_active": c.is_active,
        "conditions": c.conditions,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "steps": [
            {
                "id": s.id,
                "step_order": s.step_order,
                "step_type": s.step_type.value,
                "delay_minutes": s.delay_minutes,
                "subject": s.subject,
                "body_template": s.body_template,
            }
            for s in c.steps
        ],
    }


@router.get("/chains")
def list_chains(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {"items": [_serialize_chain(c) for c in UpsellService(db).list_chains()]}


@router.post("/chains", status_code=201)
def create_chain(
    payload: UpsellChainCreate,
    _: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    c = UpsellService(db).create_chain(
        name=payload.name,
        trigger=payload.trigger,
        description=payload.description,
        conditions=payload.conditions or {},
        steps=[s.model_dump() for s in payload.steps],
    )
    return _serialize_chain(c)


@router.patch("/chains/{chain_id}")
def update_chain(
    chain_id: int,
    payload: UpsellChainUpdate,
    _: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    c = UpsellService(db).update_chain(
        chain_id, **payload.model_dump(exclude_unset=True)
    )
    if not c:
        raise HTTPException(status_code=404, detail="Chain not found")
    return _serialize_chain(c)


@router.delete("/chains/{chain_id}", status_code=204)
def delete_chain(
    chain_id: int,
    _: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    if not UpsellService(db).delete_chain(chain_id):
        raise HTTPException(status_code=404, detail="Chain not found")


@router.post("/process-due")
def process_due(
    limit: int = Query(50, ge=1, le=500),
    _: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    return UpsellService(db).process_due(limit=limit)


@router.get("/chains/{chain_id}/metrics")
def chain_metrics(
    chain_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return UpsellService(db).chain_metrics(chain_id)


class ManualTriggerIn(BaseModel):
    trigger: UpsellTrigger
    guest_id: Optional[int] = None
    reservation_id: Optional[int] = None
    event_payload: Optional[dict] = None


@router.post("/trigger")
def manual_trigger(
    payload: ManualTriggerIn,
    _: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    runs = UpsellService(db).trigger(
        payload.trigger,
        guest_id=payload.guest_id,
        reservation_id=payload.reservation_id,
        event_payload=payload.event_payload,
    )
    return {"runs_started": len(runs), "ids": [r.id for r in runs]}
