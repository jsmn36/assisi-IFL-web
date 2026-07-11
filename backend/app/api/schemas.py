"""
API Schemas (Pydantic models)
Request/Response models for API
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


# Base schemas
class SuccessResponse(BaseModel):
    """Generic success response"""

    success: bool = True
    message: str
    data: Optional[dict] = None


class ErrorResponse(BaseModel):
    """Error response"""

    success: bool = False
    error: str
    code: str
    details: Optional[dict] = None


# Guest schemas
class GuestCreate(BaseModel):
    """Create guest request"""

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    guest_type: Optional[str] = "INDIVIDUAL"


class GuestUpdate(BaseModel):
    """Update guest request"""

    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    special_requests: Optional[str] = None


class GuestResponse(BaseModel):
    """Guest response"""

    id: int
    first_name: str
    last_name: str
    full_name: str
    email: Optional[str]
    phone: Optional[str]
    guest_type: Optional[str] = None
    is_vip: Optional[bool] = False
    total_stays: Optional[int] = 0
    total_nights: Optional[int] = 0

    class Config:
        from_attributes = True


# Reservation schemas
class ReservationCreate(BaseModel):
    """Create reservation request"""

    property_id: int
    guest_id: int
    room_type_id: int
    check_in_date: date
    check_out_date: date
    num_adults: int = Field(..., ge=1, le=10)
    num_children: int = Field(0, ge=0, le=10)
    rate_plan_id: Optional[int] = None
    nightly_rate: Optional[Decimal] = None
    source: Optional[str] = "direct"
    special_requests: Optional[str] = None

    @validator("check_out_date")
    def check_out_after_check_in(cls, v, values):
        if "check_in_date" in values and v <= values["check_in_date"]:
            raise ValueError("check_out_date must be after check_in_date")
        return v


class ReservationUpdate(BaseModel):
    """Update reservation request"""

    check_in_date: Optional[date] = None
    check_out_date: Optional[date] = None
    num_adults: Optional[int] = Field(None, ge=1, le=10)
    num_children: Optional[int] = Field(None, ge=0, le=10)
    special_requests: Optional[str] = None


class ReservationResponse(BaseModel):
    """Reservation response"""

    id: int
    confirmation_number: str
    property_id: int
    guest_id: int
    room_type_id: int
    check_in_date: date
    check_out_date: date
    number_of_nights: int
    num_adults: int
    num_children: int
    status: str
    total_amount: Decimal
    nightly_rate: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


# Room schemas
class RoomResponse(BaseModel):
    """Room response"""

    id: int
    property_id: int
    room_type_id: int
    room_number: str
    floor: Optional[int]
    building: Optional[str]
    occupancy_state: str
    condition_state: str
    is_active: bool
    is_available: bool
    current_guest: Optional[str] = None
    current_reservation: Optional[str] = None
    current_reservation_id: Optional[int] = None

    class Config:
        from_attributes = True


# Check-in schemas
class CheckInRequest(BaseModel):
    """Check-in request"""

    reservation_id: Optional[int] = None
    confirmation_number: Optional[str] = None
    room_id: Optional[int] = None
    room_number: Optional[str] = None
    post_room_charges: bool = False


class CheckInResponse(BaseModel):
    """Check-in response"""

    success: bool
    message: str
    reservation: ReservationResponse
    room_number: str
    charges_posted: int
    stay_id: Optional[int] = None
    warnings: List[str] = []


# Check-out schemas
class CheckOutRequest(BaseModel):
    """Check-out request"""

    stay_id: Optional[int] = None
    reservation_id: Optional[int] = None
    room_id: Optional[int] = None
    payment_method: Optional[str] = None
    force_checkout: bool = False


class CheckOutResponse(BaseModel):
    """Check-out response"""

    success: bool
    message: str
    bill: dict
    payment: dict
    warnings: List[str] = []


# Stay schemas
class StayResponse(BaseModel):
    """Stay response"""

    id: int
    reservation_id: int
    room_id: int
    guest_id: int
    check_in_date: date
    check_out_date: date
    status: str
    total_charges: Decimal
    number_of_nights: int

    class Config:
        from_attributes = True


# Charge schemas
class ChargeCreate(BaseModel):
    """Create charge request"""

    stay_id: Optional[int] = None  # taken from URL path, not required in body
    charge_type: str
    description: str
    amount: Decimal = Field(..., gt=0)
    quantity: int = Field(1, ge=1)


class ChargeResponse(BaseModel):
    """Charge response"""

    id: int
    stay_id: int
    charge_type: str
    description: str
    amount: Decimal
    total_amount: Decimal
    status: str
    charge_date: Optional[date]

    class Config:
        from_attributes = True
