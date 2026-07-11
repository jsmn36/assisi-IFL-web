"""
# Room API Endpoints
"""
from fastapi import APIRouter, Depends, Query, status
from typing import List, Optional
from datetime import date
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.api.dependencies import get_room_service, get_current_user, get_db
from app.api.schemas import RoomResponse, SuccessResponse
from app.services import RoomService
from app.services.audit_helper import write_audit

router = APIRouter(prefix="/rooms", tags=["Rooms"])


class RoomCreate(BaseModel):
    property_id: int
    room_type_id: int
    room_number: str
    floor: Optional[int] = None
    description: Optional[str] = None


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_room(
    data: RoomCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new room"""
    from app.models.room import Room, RoomStatus, ConditionState, OccupancyState

    room = Room(
        property_id=data.property_id,
        room_type_id=data.room_type_id,
        room_number=data.room_number,
        floor=data.floor,
        status=RoomStatus.AVAILABLE,
        condition_state=ConditionState.CLEAN,
        occupancy_state=OccupancyState.VACANT,
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    write_audit(db, "create_room", "room", current_user=current_user, resource_id=room.id,
                details=f"Room {room.room_number}")
    return room.to_dict()


@router.get("/", response_model=List[RoomResponse], summary="Get all rooms")
async def get_all_rooms(
    property_id: int = Query(1),
    skip: int = Query(0),
    limit: int = Query(100),
    service: RoomService = Depends(get_room_service),
):
    """Get all rooms for a property"""
    rooms = service.get_all_rooms(property_id=property_id, skip=skip, limit=limit)
    return [
        {
            **room.to_dict(),
            "is_available": room.is_available(),
            "current_guest": next(
                (
                    r.guest.full_name
                    for r in room.reservations
                    if r.status.value.upper() == "CHECKED_IN" and r.guest
                ),
                None,
            ),
            "current_reservation": next(
                (
                    r.confirmation_number
                    for r in room.reservations
                    if r.status.value.upper() == "CHECKED_IN"
                ),
                None,
            ),
            "current_reservation_id": next(
                (
                    r.id
                    for r in room.reservations
                    if r.status.value.upper() == "CHECKED_IN"
                ),
                None,
            ),
        }
        for room in rooms
    ]


@router.get(
    "/available", response_model=List[RoomResponse], summary="Get available rooms"
)
async def get_available_rooms(
    property_id: int = Query(...),
    room_type_id: Optional[int] = Query(None),
    check_in_date: Optional[date] = Query(None),
    check_out_date: Optional[date] = Query(None),
    service: RoomService = Depends(get_room_service),
):
    """
    # Get available rooms

    - **property_id**: Property ID (required)
    - **room_type_id**: Filter by room type
    - **check_in_date**: Check availability for date range
    - **check_out_date**: Check availability for date range
    """
    rooms = service.get_available_rooms(
        property_id=property_id,
        room_type_id=room_type_id,
        check_in_date=check_in_date,
        check_out_date=check_out_date,
    )

    return [{**room.to_dict(), "is_available": room.is_available()} for room in rooms]


@router.get(
    "/property/{property_id}/number/{room_number}",
    response_model=RoomResponse,
    summary="Get room by number",
)
async def get_room_by_number(
    property_id: int, room_number: str, service: RoomService = Depends(get_room_service)
):
    """Get room by room number"""
    room = service.get_room(room_number=room_number, property_id=property_id)
    return {**room.to_dict(), "is_available": room.is_available()}


@router.get("/housekeeping/status/{property_id}", summary="Get housekeeping status")
async def get_housekeeping_status(
    property_id: int, service: RoomService = Depends(get_room_service)
):
    """
    # Get housekeeping status summary for property

    # Returns counts by room status
    """
    result = service.get_housekeeping_status(property_id)
    return result


@router.get("/{room_id}", response_model=RoomResponse, summary="Get room by ID")
async def get_room(room_id: int, service: RoomService = Depends(get_room_service)):
    """Get room by ID"""
    room = service.get_room(room_id=room_id)
    return {**room.to_dict(), "is_available": room.is_available()}


@router.post(
    "/{room_id}/clean", response_model=SuccessResponse, summary="Mark room as clean"
)
async def mark_room_clean(
    room_id: int,
    service: RoomService = Depends(get_room_service),
    current_user: str = Depends(get_current_user),
):
    """Mark room as clean"""
    room = service.mark_room_clean(room_id, cleaned_by=current_user)
    write_audit(service.db, "mark_room_clean", "room", current_user=current_user, resource_id=room_id,
                details=f"Room {room.room_number}")
    return SuccessResponse(
        message=f"Room {room.room_number} marked as clean",
        data={"room_number": room.room_number, "condition": room.condition_state.value},
    )


@router.post(
    "/{room_id}/dirty", response_model=SuccessResponse, summary="Mark room as dirty"
)
async def mark_room_dirty(
    room_id: int,
    service: RoomService = Depends(get_room_service),
    current_user: str = Depends(get_current_user),
):
    """Mark room as dirty (needs cleaning)"""
    room = service.mark_room_dirty(room_id, marked_by=current_user)
    write_audit(service.db, "mark_room_dirty", "room", current_user=current_user, resource_id=room_id,
                details=f"Room {room.room_number}")
    return SuccessResponse(
        message=f"Room {room.room_number} marked as dirty",
        data={"room_number": room.room_number, "condition": room.condition_state.value},
    )


@router.post(
    "/{room_id}/inspected",
    response_model=SuccessResponse,
    summary="Mark room as inspected",
)
async def mark_room_inspected(
    room_id: int,
    service: RoomService = Depends(get_room_service),
    current_user: str = Depends(get_current_user),
):
    """Mark room as inspected"""
    room = service.mark_room_inspected(room_id, inspected_by=current_user)
    write_audit(service.db, "mark_room_inspected", "room", current_user=current_user, resource_id=room_id,
                details=f"Room {room.room_number}")
    return SuccessResponse(
        message=f"Room {room.room_number} marked as inspected",
        data={"room_number": room.room_number, "condition": room.condition_state.value},
    )


@router.post(
    "/{room_id}/out-of-order",
    response_model=SuccessResponse,
    summary="Take room out of order",
)
async def take_room_out_of_order(
    room_id: int,
    reason: str = Query(..., min_length=1),
    service: RoomService = Depends(get_room_service),
    current_user: str = Depends(get_current_user),
):
    """Take room out of order (maintenance, damage, etc.)"""
    room = service.take_room_out_of_order(room_id, reason=reason, taken_by=current_user)
    write_audit(service.db, "room_out_of_order", "room", current_user=current_user, resource_id=room_id,
                details=f"Room {room.room_number}: {reason}")
    return SuccessResponse(
        message=f"Room {room.room_number} taken out of order",
        data={"room_number": room.room_number, "reason": reason},
    )


@router.post(
    "/{room_id}/return-to-service",
    response_model=SuccessResponse,
    summary="Return room to service",
)
async def return_room_to_service(
    room_id: int,
    service: RoomService = Depends(get_room_service),
    current_user: str = Depends(get_current_user),
):
    """Return room to service from out of order"""
    room = service.return_room_to_service(room_id, returned_by=current_user)
    write_audit(service.db, "room_return_to_service", "room", current_user=current_user, resource_id=room_id,
                details=f"Room {room.room_number}")
    return SuccessResponse(
        message=f"Room {room.room_number} returned to service",
        data={"room_number": room.room_number, "occupancy": room.occupancy_state.value},
    )
