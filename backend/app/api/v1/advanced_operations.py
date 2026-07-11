"""
# Advanced Operations API Endpoints
No-show, Waitlist, Night Audit, Room Changes
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
from datetime import date
from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.services import (
    NoShowService,
    WaitlistService,
    NightAuditService,
    BusinessDayService,
    RoomChangeService,
)
from sqlalchemy.orm import Session

router = APIRouter(prefix="/operations", tags=["Advanced Operations"])


def _user_id_int(current_user) -> int | None:
    uid = getattr(current_user, "id", None)
    if uid is None:
        return None
    if isinstance(uid, int):
        return uid
    try:
        return int(uid)
    except (TypeError, ValueError):
        return None


def _gate_actor_id(current_user: User) -> int:
    """JWT-resolved user id for ``GateContext.user_id`` (e.g. ManualOverrideGate)."""
    return int(current_user.id)


# === No-Show Endpoints ===


@router.post(
    "/reservations/{reservation_id}/no-show",
    summary="Mark reservation as no-show",
)
async def mark_no_show(
    reservation_id: int,
    reason: Optional[str] = Query(None),
    waive_fee: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Mark reservation as no-show with optional fee waiver."""
    service = NoShowService(db)
    user_id = str(current_user.id) if hasattr(current_user, "id") else "system"
    return service.mark_no_show(reservation_id, user_id, reason, waive_fee)


@router.get(
    "/no-shows/report",
    summary="Get no-show report",
)
async def get_no_show_report(
    property_id: int = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
):
    """Get no-show statistics for a date range."""
    service = NoShowService(db)
    return service.get_no_show_report(property_id, start_date, end_date)


# === Waitlist Endpoints ===


@router.post(
    "/waitlist",
    status_code=status.HTTP_201_CREATED,
    summary="Add guest to waitlist",
)
async def add_to_waitlist(
    property_id: int = Query(...),
    guest_id: int = Query(...),
    room_type_id: int = Query(...),
    check_in_date: date = Query(...),
    check_out_date: date = Query(...),
    num_adults: int = Query(...),
    num_children: int = Query(0),
    priority: int = Query(0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Add a guest to the waitlist for a room type and date range."""
    service = WaitlistService(db)
    user_id = str(current_user.id) if hasattr(current_user, "id") else "system"
    return service.add_to_waitlist(
        property_id,
        guest_id,
        room_type_id,
        check_in_date,
        check_out_date,
        num_adults,
        num_children,
        priority,
        user_id,
    )


@router.get(
    "/waitlist",
    summary="Get waitlist entries",
)
async def get_waitlist(
    property_id: int = Query(...),
    room_type_id: Optional[int] = Query(None),
    check_in_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
):
    """Return waitlist entries, optionally filtered by room type or date."""
    service = WaitlistService(db)
    return service.get_waitlist(property_id, room_type_id, check_in_date)


@router.post(
    "/waitlist/{waitlist_id}/promote",
    summary="Promote waitlist entry to reservation",
)
async def promote_from_waitlist(
    waitlist_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Convert a waitlist entry into a confirmed reservation."""
    service = WaitlistService(db)
    user_id = str(current_user.id) if hasattr(current_user, "id") else "system"
    return service.promote_from_waitlist(waitlist_id, user_id)


@router.delete(
    "/waitlist/{waitlist_id}",
    summary="Remove entry from waitlist",
)
async def remove_from_waitlist(
    waitlist_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Remove a guest from the waitlist."""
    service = WaitlistService(db)
    user_id = str(current_user.id) if hasattr(current_user, "id") else "system"
    success = service.remove_from_waitlist(waitlist_id, user_id)
    return {"success": success}


# === Night Audit Endpoints ===


@router.post(
    "/night-audit",
    summary="Run night audit",
)
async def run_night_audit(
    property_id: int = Query(...),
    audit_date: date = Query(...),
    manual_override_justification: Optional[str] = Query(
        None,
        description="If set with target, runs ManualOverrideGate first (audit trail).",
    ),
    manual_override_target: Optional[str] = Query(
        None,
        description="Gate name being overridden (e.g. NightAuditGate).",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Execute the night audit process for a given property and date."""
    if (manual_override_justification or manual_override_target) and not (
        manual_override_justification and manual_override_target
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "manual_override_justification and manual_override_target "
                "must both be provided or both omitted"
            ),
        )
    service = NightAuditService(db)
    run_by = str(current_user.id)
    return service.run_night_audit(
        property_id,
        audit_date,
        run_by=run_by,
        user_id=_gate_actor_id(current_user),
        manual_override_justification=manual_override_justification,
        manual_override_target=manual_override_target,
    )


@router.post(
    "/night-audit/close-day",
    summary="Close current business day",
)
async def close_business_day(
    property_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Enforces DayClose gate logic. Rolls business day pointer exclusively if 8 checks cleanly resolved.
    """
    service = BusinessDayService(db)
    return service.close_business_day(property_id, _gate_actor_id(current_user))


@router.get(
    "/night-audit/report",
    summary="Get night audit report",
)
async def get_audit_report(
    property_id: int = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
):
    """Return aggregated audit statistics for a date range."""
    service = NightAuditService(db)
    return service.generate_audit_report(property_id, start_date, end_date)


# === Room Change Endpoints ===


@router.post(
    "/stays/{stay_id}/change-room",
    summary="Change guest room",
)
async def change_room(
    stay_id: int,
    new_room_id: int,
    reason: str,
    charge_fee: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Move a guest to a different room during their stay."""
    service = RoomChangeService(db)
    user_id = str(current_user.id) if hasattr(current_user, "id") else "system"
    return service.change_room(stay_id, new_room_id, reason, user_id, charge_fee)


@router.get(
    "/stays/{stay_id}/validate-room-change",
    summary="Validate a proposed room change",
)
async def validate_room_change(
    stay_id: int,
    new_room_id: int = Query(...),
    db: Session = Depends(get_db),
):
    """Check whether a room change is possible before executing it."""
    service = RoomChangeService(db)
    return service.validate_room_change(stay_id, new_room_id)


@router.get(
    "/room-changes/history",
    summary="Get room change history",
)
async def get_room_change_history(
    property_id: int = Query(...),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Return recent room change events for a property."""
    service = RoomChangeService(db)
    return service.get_room_change_history(property_id, limit)
