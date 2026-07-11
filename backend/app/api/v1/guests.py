from fastapi import APIRouter, Depends, Query, status
from typing import List, Optional

from app.api.dependencies import get_guest_service, get_current_user
from app.services.audit_helper import write_audit
from app.api.schemas import (
    GuestCreate,
    GuestUpdate,
    GuestResponse,
    ReservationResponse,
    SuccessResponse,
)
from app.services import GuestService
from app.models import GuestType

router = APIRouter(prefix="/guests", tags=["Guests"])


@router.post(
    "",
    response_model=GuestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create guest",
)
async def create_guest(
    data: GuestCreate,
    service: GuestService = Depends(get_guest_service),
    current_user=Depends(get_current_user),
):
    """
    # Create a new guest

    - **first_name**: First name (required)
    - **last_name**: Last name (required)
    - **email**: Email address (optional but recommended)
    - **phone**: Phone number (optional)
    - **guest_type**: Type of guest (individual/corporate/group)
    """
    guest_type = GuestType(data.guest_type) if data.guest_type else GuestType.INDIVIDUAL

    guest = service.create_guest(
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        phone=data.phone,
        guest_type=guest_type,
    )
    write_audit(service.db, "create_guest", "guest",
                current_user=current_user, resource_id=guest.id,
                details=guest.full_name)
    return guest


@router.get(
    "/{guest_id}",
    response_model=GuestResponse,
    summary="Get guest by ID",
)
async def get_guest(
    guest_id: int,
    service: GuestService = Depends(get_guest_service),
):
    """Get guest by ID"""
    return service.get_guest(guest_id=guest_id)


@router.get(
    "/email/{email}",
    response_model=GuestResponse,
    summary="Get guest by email",
)
async def get_guest_by_email(
    email: str,
    service: GuestService = Depends(get_guest_service),
):
    """Get guest by email address"""
    return service.get_guest(email=email)


@router.get(
    "",
    response_model=List[GuestResponse],
    summary="Search guests",
)
async def search_guests(
    query: Optional[str] = Query(None, description="Search in name or email"),
    email: Optional[str] = Query(None),
    phone: Optional[str] = Query(None),
    is_vip: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    service: GuestService = Depends(get_guest_service),
):
    """
    # Search guests with filters

    - **query**: Search in name or email
    - **email**: Filter by email
    - **phone**: Filter by phone
    - **is_vip**: Filter by VIP status
    - **limit**: Maximum results
    """
    return service.search_guests(
        query=query,
        email=email,
        phone=phone,
        is_vip=is_vip,
        limit=limit,
    )


@router.put(
    "/{guest_id}",
    response_model=GuestResponse,
    summary="Update guest",
)
async def update_guest(
    guest_id: int,
    data: GuestUpdate,
    service: GuestService = Depends(get_guest_service),
    current_user=Depends(get_current_user),
):
    """Update guest details"""
    update_data = data.dict(exclude_none=True)
    guest = service.update_guest(guest_id=guest_id, **update_data)
    write_audit(service.db, "update_guest", "guest",
                current_user=current_user, resource_id=guest_id)
    return guest


@router.get(
    "/{guest_id}/reservations",
    response_model=List[ReservationResponse],
    summary="Get guest reservations",
)
async def get_guest_reservations(
    guest_id: int,
    limit: int = Query(50, ge=1, le=500),
    service: GuestService = Depends(get_guest_service),
):
    """Get all reservations for guest"""
    return service.get_guest_reservations(
        guest_id=guest_id,
        limit=limit,
    )


@router.post(
    "/{guest_id}/blacklist",
    response_model=SuccessResponse,
    summary="Blacklist guest",
)
async def blacklist_guest(
    guest_id: int,
    reason: str = Query(..., min_length=1),
    service: GuestService = Depends(get_guest_service),
    current_user: str = Depends(get_current_user),
):
    """Blacklist a guest"""
    guest = service.blacklist_guest(
        guest_id=guest_id,
        reason=reason,
        blacklisted_by=current_user,
    )

    write_audit(service.db, "blacklist_guest", "guest",
                current_user=current_user, resource_id=guest_id, details=reason)
    return SuccessResponse(
        message=f"Guest {guest.full_name} blacklisted",
        data={"guest_id": guest.id, "reason": reason},
    )


@router.delete(
    "/{guest_id}/blacklist",
    response_model=SuccessResponse,
    summary="Remove guest from blacklist",
)
async def remove_from_blacklist(
    guest_id: int,
    service: GuestService = Depends(get_guest_service),
    current_user: str = Depends(get_current_user),
):
    """Remove guest from blacklist"""
    guest = service.remove_from_blacklist(
        guest_id=guest_id,
        removed_by=current_user,
    )

    write_audit(service.db, "remove_from_blacklist", "guest",
                current_user=current_user, resource_id=guest_id)
    return SuccessResponse(
        message=f"Guest {guest.full_name} removed from blacklist",
        data={"guest_id": guest.id},
    )


@router.delete(
    "/{guest_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete guest",
)
async def delete_guest(
    guest_id: int,
    service: GuestService = Depends(get_guest_service),
    current_user=Depends(get_current_user),
):
    """Permanently delete a guest record."""
    service.delete_guest(guest_id=guest_id)
    write_audit(service.db, "delete_guest", "guest",
                current_user=current_user, resource_id=guest_id)
