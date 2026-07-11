"""Suppression list API.

Manage opt-out / bounce / complaint records that block outbound mail.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db, require_role
from app.models import User
from app.models.suppression import SuppressionChannel, SuppressionReason
from app.services.suppression_service import SuppressionService

router = APIRouter(prefix="/suppressions", tags=["Notifications — Suppressions"])


class SuppressionOut(BaseModel):
    id: int
    address: str
    channel: SuppressionChannel
    reason: SuppressionReason
    notes: Optional[str] = None
    source: Optional[str] = None
    created_at: str
    created_by: Optional[int] = None

    class Config:
        from_attributes = True


class SuppressionCreate(BaseModel):
    address: str = Field(..., min_length=3)
    channel: SuppressionChannel = SuppressionChannel.EMAIL
    reason: SuppressionReason = SuppressionReason.MANUAL
    notes: Optional[str] = None


class SuppressionBulkCreate(BaseModel):
    addresses: List[str]
    channel: SuppressionChannel = SuppressionChannel.EMAIL
    reason: SuppressionReason = SuppressionReason.MANUAL


class SuppressionListResponse(BaseModel):
    items: List[dict]
    total: int
    limit: int
    offset: int


def _serialize(row) -> dict:
    return {
        "id": row.id,
        "address": row.address,
        "channel": row.channel.value if hasattr(row.channel, "value") else row.channel,
        "reason": row.reason.value if hasattr(row.reason, "value") else row.reason,
        "notes": row.notes,
        "source": row.source,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "created_by": row.created_by,
    }


@router.get("", response_model=SuppressionListResponse)
def list_suppressions(
    channel: Optional[SuppressionChannel] = None,
    reason: Optional[SuppressionReason] = None,
    search: Optional[str] = Query(None, min_length=1),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    _: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    rows, total = SuppressionService(db).list(
        channel=channel, reason=reason, search=search, limit=limit, offset=offset
    )
    return SuppressionListResponse(
        items=[_serialize(r) for r in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=dict, status_code=201)
def create_suppression(
    payload: SuppressionCreate,
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    row = SuppressionService(db).add(
        address=payload.address,
        channel=payload.channel,
        reason=payload.reason,
        notes=payload.notes,
        source="ui",
        created_by=current_user.id,
    )
    return _serialize(row)


@router.post("/bulk", response_model=dict)
def bulk_create_suppressions(
    payload: SuppressionBulkCreate,
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    added = SuppressionService(db).bulk_import(
        addresses=payload.addresses,
        channel=payload.channel,
        reason=payload.reason,
        created_by=current_user.id,
    )
    return {"added": added, "skipped": len(payload.addresses) - added}


@router.delete("/{suppression_id}", status_code=204)
def delete_suppression(
    suppression_id: int,
    _: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    if not SuppressionService(db).remove(suppression_id):
        raise HTTPException(status_code=404, detail="Suppression not found")


@router.get("/check", response_model=dict)
def check_address(
    address: str = Query(..., min_length=3),
    channel: SuppressionChannel = SuppressionChannel.EMAIL,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lightweight pre-send check used by other services."""
    row = SuppressionService(db).is_suppressed(address, channel)
    return {
        "address": address,
        "channel": channel.value,
        "suppressed": bool(row),
        "reason": row.reason.value if row else None,
    }
