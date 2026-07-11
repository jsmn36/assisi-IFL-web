"""Allocation pool / oversell prevention API."""
from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db, require_role
from app.models import User
from app.models.allocation import HoldReason
from app.services.allocation_service import AllocationService

router = APIRouter(prefix="/allocations", tags=["Allocation Pool"])


class AllocationIn(BaseModel):
    room_type_id: int
    night: date
    total_inventory: int = Field(..., ge=0)
    safety_stock: int = Field(0, ge=0)
    inbound: int = Field(0, ge=0)
    quarantine: int = Field(0, ge=0)


class ChannelBufferIn(BaseModel):
    room_type_id: int
    night: date
    channel: str
    max_sellable: int = Field(..., ge=0)


class HoldIn(BaseModel):
    room_type_id: int
    night_from: date
    night_to: date
    quantity: int = Field(1, ge=1)
    reason: HoldReason = HoldReason.OUT_OF_ORDER
    note: Optional[str] = None


def _serialize_snapshot(s) -> dict:
    return {
        "room_type_id": s.room_type_id,
        "night": s.night.isoformat(),
        "total_inventory": s.total_inventory,
        "safety_stock": s.safety_stock,
        "inbound": s.inbound,
        "quarantine": s.quarantine,
        "reserved": s.reserved,
        "holds": s.holds,
        "base_sellable": s.base_sellable,
        "by_channel": s.by_channel,
    }


@router.post("", status_code=201)
def upsert_allocation(
    payload: AllocationIn,
    _: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    a = AllocationService(db).upsert(**payload.model_dump())
    return {"id": a.id, "room_type_id": a.room_type_id, "night": a.night.isoformat()}


@router.post("/channel-buffers", status_code=201)
def upsert_channel_buffer(
    payload: ChannelBufferIn,
    _: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    b = AllocationService(db).set_channel_buffer(**payload.model_dump())
    return {
        "id": b.id,
        "room_type_id": b.room_type_id,
        "night": b.night.isoformat(),
        "channel": b.channel,
        "max_sellable": b.max_sellable,
    }


@router.post("/holds", status_code=201)
def create_hold(
    payload: HoldIn,
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    h = AllocationService(db).create_hold(
        **payload.model_dump(), created_by=current_user.id
    )
    return {
        "id": h.id,
        "room_type_id": h.room_type_id,
        "night_from": h.night_from.isoformat(),
        "night_to": h.night_to.isoformat(),
        "quantity": h.quantity,
        "reason": h.reason.value,
    }


@router.post("/holds/{hold_id}/release")
def release_hold(
    hold_id: int,
    _: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    h = AllocationService(db).release_hold(hold_id)
    if not h:
        raise HTTPException(status_code=404, detail="Not found")
    return {"id": h.id, "released_at": h.released_at.isoformat() if h.released_at else None}


@router.get("/snapshot")
def snapshot(
    room_type_id: int = Query(...),
    night: date = Query(...),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _serialize_snapshot(AllocationService(db).snapshot(room_type_id, night))


@router.get("/range")
def range_snapshot(
    room_type_id: int = Query(...),
    start: date = Query(...),
    end: date = Query(...),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if end < start:
        raise HTTPException(status_code=400, detail="end < start")
    nights = []
    day = start
    while day <= end:
        nights.append(day)
        day = day + timedelta(days=1)
    snaps = AllocationService(db).range_snapshot(room_type_id, nights)
    return {"rows": [_serialize_snapshot(s) for s in snaps]}


@router.get("/safe-to-sell")
def safe_to_sell(
    room_type_id: int = Query(...),
    night: date = Query(...),
    channel: Optional[str] = Query(None),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    n = AllocationService(db).safe_to_sell(room_type_id, night, channel=channel)
    return {
        "room_type_id": room_type_id,
        "night": night.isoformat(),
        "channel": channel,
        "safe_to_sell": n,
    }
