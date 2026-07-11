"""
Room Type Management API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user
from app.models.room_type import RoomType

router = APIRouter(prefix="/room-types", tags=["Room Types"])


class RoomTypeCreate(BaseModel):
    property_id: int
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    base_price: Optional[float] = 0.0
    max_occupancy: Optional[int] = 2
    max_adults: Optional[int] = 2
    max_children: Optional[int] = 1
    bed_type: Optional[str] = None


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_room_type(
    data: RoomTypeCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new room type"""
    rt = RoomType(
        property_id=data.property_id,
        name=data.name,
        code=data.code,
        description=data.description,
        base_price=data.base_price,
        max_occupancy=data.max_occupancy,
        max_adults=data.max_adults,
        max_children=data.max_children,
        bed_type=data.bed_type,
    )
    db.add(rt)
    db.commit()
    db.refresh(rt)
    return rt.to_dict()


@router.get("/")
async def list_room_types(
    property_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List room types, optionally filtered by property"""
    q = db.query(RoomType).filter(RoomType.is_active.is_(True))
    if property_id:
        q = q.filter(RoomType.property_id == property_id)
    return [rt.to_dict() for rt in q.all()]


@router.get("/{room_type_id}")
async def get_room_type(
    room_type_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get room type by ID"""
    rt = db.query(RoomType).filter(RoomType.id == room_type_id).first()
    if not rt:
        raise HTTPException(status_code=404, detail="Room type not found")
    return rt.to_dict()
