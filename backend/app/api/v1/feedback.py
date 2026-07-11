"""Guest feedback close-loop API."""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db, require_role
from app.models import User
from app.models.feedback import FeedbackChannel, FeedbackSentiment, ResolutionStatus
from app.services.feedback_service import FeedbackService

router = APIRouter(prefix="/feedback", tags=["Guest Feedback"])


class FeedbackIn(BaseModel):
    channel: FeedbackChannel = FeedbackChannel.MANUAL
    guest_id: Optional[int] = None
    reservation_id: Optional[int] = None
    nps_score: Optional[int] = Field(None, ge=0, le=10)
    rating_1_5: Optional[int] = Field(None, ge=1, le=5)
    sentiment: FeedbackSentiment = FeedbackSentiment.NEUTRAL
    title: Optional[str] = None
    body: Optional[str] = None
    tags: Optional[str] = None
    default_owner_user_id: Optional[int] = None


class ResolutionUpdate(BaseModel):
    status: Optional[ResolutionStatus] = None
    owner_user_id: Optional[int] = None
    due_date: Optional[datetime] = None
    resolution_summary: Optional[str] = None


class ResolveIn(BaseModel):
    resolution_summary: str = Field(..., min_length=1)


def _serialize(fb) -> dict:
    return {
        "id": fb.id,
        "guest_id": fb.guest_id,
        "reservation_id": fb.reservation_id,
        "channel": fb.channel.value,
        "nps_score": fb.nps_score,
        "rating_1_5": fb.rating_1_5,
        "sentiment": fb.sentiment.value,
        "title": fb.title,
        "body": fb.body,
        "tags": fb.tags,
        "created_at": fb.created_at.isoformat() if fb.created_at else None,
        "resolution": _serialize_resolution(fb.resolution) if fb.resolution else None,
    }


def _serialize_resolution(res) -> dict:
    return {
        "id": res.id,
        "status": res.status.value,
        "owner_user_id": res.owner_user_id,
        "due_date": res.due_date.isoformat() if res.due_date else None,
        "resolution_summary": res.resolution_summary,
        "guest_notified_at": res.guest_notified_at.isoformat() if res.guest_notified_at else None,
        "resolved_at": res.resolved_at.isoformat() if res.resolved_at else None,
        "resolved_by": res.resolved_by,
    }


@router.post("", status_code=201)
def submit_feedback(
    payload: FeedbackIn,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    fb = FeedbackService(db).submit(**payload.model_dump())
    return _serialize(fb)


@router.get("")
def list_feedback(
    sentiment: Optional[FeedbackSentiment] = None,
    guest_id: Optional[int] = None,
    with_open_task: Optional[bool] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows, total = FeedbackService(db).list(
        sentiment=sentiment,
        guest_id=guest_id,
        with_open_task=with_open_task,
        limit=limit,
        offset=offset,
    )
    return {
        "items": [_serialize(r) for r in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{feedback_id}")
def get_feedback(
    feedback_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    fb = FeedbackService(db).get(feedback_id)
    if not fb:
        raise HTTPException(status_code=404, detail="Not found")
    return _serialize(fb)


@router.patch("/{feedback_id}/resolution")
def update_resolution(
    feedback_id: int,
    payload: ResolutionUpdate,
    _: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    res = FeedbackService(db).update_resolution(
        feedback_id, **payload.model_dump(exclude_unset=True)
    )
    if not res:
        raise HTTPException(status_code=404, detail="Not found")
    return _serialize_resolution(res)


@router.post("/{feedback_id}/resolve")
def resolve(
    feedback_id: int,
    payload: ResolveIn,
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    res = FeedbackService(db).resolve_and_notify(
        feedback_id,
        resolution_summary=payload.resolution_summary,
        actor_user_id=current_user.id,
    )
    if not res:
        raise HTTPException(status_code=404, detail="Not found")
    return _serialize_resolution(res)


@router.get("/_/overdue")
def overdue(
    _: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    rows = FeedbackService(db).overdue()
    return {"items": [_serialize_resolution(r) for r in rows]}
