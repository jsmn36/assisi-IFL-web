from fastapi import APIRouter, HTTPException, Query, Depends
from datetime import date, timezone
from typing import List, Optional
from pydantic import BaseModel, UUID4
import hashlib
import json
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.dependencies import get_db
from app.models.room import Room
from app.models.reservation import Reservation
from app.models.enums import ReservationStatus

router = APIRouter()


# Schema for return
class AvailabilitySnapshot(BaseModel):
    date: date
    available_rooms: int
    total_rooms: int
    occupied_rooms: int


class AvailabilityQueryResponse(BaseModel):
    property_id: str
    room_type_id: int
    availability: List[AvailabilitySnapshot]
    checksum: str
    generated_at: datetime


@router.get("/query", response_model=AvailabilityQueryResponse)
async def query_availability(
    property_id: str, room_type_id: int, date: date, db: Session = Depends(get_db)
):
    """
    Sovereign Source of Truth.
    Queries the core PMS DB. Returns a snapshot of room availability for a date.
    """
    # 1. Total Rooms
    total_rooms = (
        db.query(Room)
        .filter(
            Room.property_id == int(property_id)
            if property_id.isdigit()
            else 1,  # hardcoded 1 for MVP property
            Room.room_type_id == room_type_id,
            Room.is_active == True,
        )
        .count()
    )

    # 2. Occupied Rooms
    # Occupied if there is a reservation intersecting the date
    occupied_rooms = (
        db.query(Reservation)
        .filter(
            Reservation.room_type_id == room_type_id,
            Reservation.check_in_date <= date,
            Reservation.check_out_date > date,
            Reservation.status.in_(
                [ReservationStatus.CONFIRMED, ReservationStatus.CHECKED_IN]
            ),
        )
        .count()
    )

    available_rooms = max(0, total_rooms - occupied_rooms)

    snapshot = AvailabilitySnapshot(
        date=date,
        available_rooms=available_rooms,
        total_rooms=total_rooms,
        occupied_rooms=occupied_rooms,
    )

    payload_to_hash = {
        "property_id": property_id,
        "room_type_id": room_type_id,
        "date": date.isoformat(),
        "available_rooms": available_rooms,
        "total_rooms": total_rooms,
    }
    checksum = hashlib.sha256(
        json.dumps(payload_to_hash, sort_keys=True).encode("utf-8")
    ).hexdigest()

    return AvailabilityQueryResponse(
        property_id=property_id,
        room_type_id=room_type_id,
        availability=[snapshot],
        checksum=checksum,
        generated_at=datetime.now(timezone.utc),
    )
