"""Compliance Calendar REST API."""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db, require_role
from app.models import User
from app.models.compliance_calendar import (
    ComplianceItem,
    ComplianceItemCategory,
    ComplianceItemStatus,
)
from app.services.compliance_calendar_service import ComplianceCalendarService

router = APIRouter(prefix="/compliance-calendar", tags=["Compliance Calendar"])


def _serialize(item: ComplianceItem) -> dict:
    return {
        "id": item.id,
        "title": item.title,
        "description": item.description,
        "category": item.category.value if item.category else None,
        "status": item.status.value if item.status else None,
        "owner_user_id": item.owner_user_id,
        "due_date": item.due_date.isoformat() if item.due_date else None,
        "recurrence_months": item.recurrence_months,
        "reminder_90d_sent_at": item.reminder_90d_sent_at.isoformat()
        if item.reminder_90d_sent_at
        else None,
        "reminder_30d_sent_at": item.reminder_30d_sent_at.isoformat()
        if item.reminder_30d_sent_at
        else None,
        "reminder_7d_sent_at": item.reminder_7d_sent_at.isoformat()
        if item.reminder_7d_sent_at
        else None,
        "completed_at": item.completed_at.isoformat() if item.completed_at else None,
        "completed_by": item.completed_by,
        "completion_evidence_url": item.completion_evidence_url,
        "notes": item.notes,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


class ComplianceItemCreate(BaseModel):
    title: str = Field(..., min_length=2)
    description: Optional[str] = None
    category: ComplianceItemCategory = ComplianceItemCategory.OTHER
    due_date: datetime
    owner_user_id: Optional[int] = None
    recurrence_months: Optional[int] = None


class ComplianceItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[ComplianceItemCategory] = None
    status: Optional[ComplianceItemStatus] = None
    due_date: Optional[datetime] = None
    owner_user_id: Optional[int] = None
    recurrence_months: Optional[int] = None
    notes: Optional[str] = None


class CompleteItemPayload(BaseModel):
    evidence_url: Optional[str] = None


@router.get("")
def list_items(
    status: Optional[ComplianceItemStatus] = None,
    category: Optional[ComplianceItemCategory] = None,
    owner_user_id: Optional[int] = None,
    within_days: Optional[int] = Query(None, ge=1, le=730),
    include_done: bool = False,
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows, total = ComplianceCalendarService(db).list(
        status=status,
        category=category,
        owner_user_id=owner_user_id,
        within_days=within_days,
        include_done=include_done,
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
def create_item(
    payload: ComplianceItemCreate,
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    item = ComplianceCalendarService(db).create(
        title=payload.title,
        description=payload.description,
        category=payload.category,
        due_date=payload.due_date,
        owner_user_id=payload.owner_user_id,
        recurrence_months=payload.recurrence_months,
        created_by=current_user.id,
    )
    return _serialize(item)


@router.patch("/{item_id}")
def update_item(
    item_id: int,
    payload: ComplianceItemUpdate,
    _: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    item = ComplianceCalendarService(db).update(
        item_id, **payload.model_dump(exclude_unset=True)
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return _serialize(item)


@router.post("/{item_id}/complete")
def complete_item(
    item_id: int,
    payload: CompleteItemPayload,
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    item = ComplianceCalendarService(db).mark_done(
        item_id,
        completed_by=current_user.id,
        evidence_url=payload.evidence_url,
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return _serialize(item)


@router.delete("/{item_id}", status_code=204)
def delete_item(
    item_id: int,
    _: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    if not ComplianceCalendarService(db).delete(item_id):
        raise HTTPException(status_code=404, detail="Item not found")


@router.post("/sweep")
def trigger_sweep(
    _: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    """Mark past-due items as OVERDUE and return reminder candidates."""
    svc = ComplianceCalendarService(db)
    sweep_stats = svc.sweep()
    pending = svc.pending_reminders()
    return {
        **sweep_stats,
        "pending_reminders": [
            {"item_id": item.id, "title": item.title, "threshold_days": days}
            for item, days in pending
        ],
    }
