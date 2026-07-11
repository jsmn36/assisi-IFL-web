from fastapi import APIRouter, Depends, Query, status, HTTPException
from typing import List, Optional
from datetime import date

from app.api.dependencies import get_stay_service, get_current_user
from app.api.schemas import (
    StayResponse,
    ChargeCreate,
    ChargeResponse,
    SuccessResponse,
)
from app.services import StayService
from app.models import ChargeType

router = APIRouter(
    prefix="/stays",
    tags=["Stays"],
)


@router.get(
    "/{stay_id}",
    response_model=StayResponse,
    summary="Get stay by ID",
)
async def get_stay(
    stay_id: int,
    service: StayService = Depends(get_stay_service),
):
    """Get stay by ID."""
    return service.get_stay(stay_id)


@router.get(
    "",
    response_model=List[StayResponse],
    summary="Get active stays",
)
async def get_active_stays(
    property_id: Optional[int] = Query(None, description="Filter by property"),
    room_id: Optional[int] = Query(None, description="Filter by room"),
    service: StayService = Depends(get_stay_service),
):
    """
    Get active (checked-in) stays.
    """
    return service.get_active_stays(
        property_id=property_id,
        room_id=room_id,
    )


@router.get(
    "/date/{property_id}/{target_date}",
    response_model=List[StayResponse],
    summary="Get stays by date",
)
async def get_stays_by_date(
    property_id: int,
    target_date: date,
    service: StayService = Depends(get_stay_service),
):
    """Get all stays for a specific date."""
    return service.get_stays_by_date(
        property_id=property_id,
        target_date=target_date,
    )


@router.post(
    "/{stay_id}/charges",
    response_model=ChargeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add charge to stay",
)
async def add_charge(
    stay_id: int,
    data: ChargeCreate,
    service: StayService = Depends(get_stay_service),
    current_user: str = Depends(get_current_user),
):
    """Add a charge to a stay."""
    try:
        charge_type = ChargeType(data.charge_type.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid charge type: {data.charge_type}. Valid: {[e.value for e in ChargeType]}",
        )

    return service.add_charge(
        stay_id=stay_id,
        charge_type=charge_type,
        description=data.description,
        amount=data.amount,
        created_by=str(current_user.id) if hasattr(current_user, "id") else "system",
    )


@router.post(
    "/{stay_id}/post-room-charges",
    response_model=SuccessResponse,
    summary="Post room charges",
)
async def post_room_charges(
    stay_id: int,
    service: StayService = Depends(get_stay_service),
    current_user: str = Depends(get_current_user),
):
    """Post nightly room charges for a stay."""
    charges = service.post_room_charges(
        stay_id=stay_id,
        posted_by=current_user,
    )

    return SuccessResponse(
        message=f"Posted {len(charges)} room charges",
        data={"charges_posted": len(charges)},
    )
