"""
Property Management API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user
from app.models.property import Property

router = APIRouter(prefix="/properties", tags=["Properties"])


class PropertyCreate(BaseModel):
    name: str
    code: str
    timezone: Optional[str] = "UTC"
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    currency: Optional[str] = "USD"


class PropertyResponse(BaseModel):
    id: int
    name: str
    code: str
    timezone: Optional[str] = None
    address_line1: Optional[str] = None
    city: Optional[str] = None
    is_active: bool = True

    class Config:
        from_attributes = True


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_property(
    data: PropertyCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new property"""
    existing = db.query(Property).filter(Property.code == data.code).first()
    if existing:
        return existing.to_dict()
    prop = Property(
        name=data.name,
        code=data.code,
        timezone=data.timezone,
        address_line1=data.address,
        city=data.city,
        state=data.state,
        country=data.country,
        phone=data.phone,
        email=data.email,
        currency=data.currency or "USD",
    )
    db.add(prop)
    db.commit()
    db.refresh(prop)
    return prop.to_dict()


@router.get("/")
async def list_properties(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all properties"""
    props = db.query(Property).filter(Property.is_active.is_(True)).all()
    return [p.to_dict() for p in props]


@router.get("/{property_id}")
async def get_property(
    property_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get property by ID"""
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return prop.to_dict()
