from fastapi import APIRouter, Depends, Query, status, HTTPException
from typing import List, Optional
from datetime import date

from app.api.dependencies import get_reservation_service, get_current_user
from app.api.schemas import (
    ReservationCreate,
    ReservationUpdate,
    ReservationResponse,
)
from app.services import ReservationService
from app.models import ReservationStatus
from app.services.base_service import BusinessRuleError
from app.services.audit_helper import write_audit

router = APIRouter(prefix="/reservations", tags=["Reservations"])


@router.post(
    "",
    response_model=ReservationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create reservation",
)
async def create_reservation(
    data: ReservationCreate,
    service: ReservationService = Depends(get_reservation_service),
    current_user: dict = Depends(get_current_user),
):
    """
    # Create a new reservation.

    - **property_id**: Property ID
    - **guest_id**: Guest ID
    - **room_type_id**: Room type ID
    - **check_in_date**: Check-in date
    - **check_out_date**: Check-out date
    - **num_adults**: Number of adults
    - **num_children**: Number of children
    """
    reservation = service.create_reservation(
        property_id=data.property_id,
        guest_id=data.guest_id,
        room_type_id=data.room_type_id,
        check_in_date=data.check_in_date,
        check_out_date=data.check_out_date,
        num_adults=data.num_adults,
        num_children=data.num_children,
        rate_plan_id=data.rate_plan_id,
        nightly_rate=data.nightly_rate,
        source=data.source,
        special_requests=data.special_requests,
        created_by=str(current_user.id) if hasattr(current_user, "id") else "system",
    )
    write_audit(service.db, "create_reservation", "reservation",
                current_user=current_user, resource_id=reservation.id,
                details=f"Confirmation: {reservation.confirmation_number}")
    return reservation


@router.get(
    "/{reservation_id}",
    response_model=ReservationResponse,
    summary="Get reservation by ID",
)
async def get_reservation(
    reservation_id: int,
    service: ReservationService = Depends(get_reservation_service),
):
    """Get reservation by ID."""
    return service.get_reservation(reservation_id=reservation_id)


@router.get(
    "/confirmation/{confirmation_number}",
    response_model=ReservationResponse,
    summary="Get reservation by confirmation number",
)
async def get_reservation_by_confirmation(
    confirmation_number: str,
    service: ReservationService = Depends(get_reservation_service),
):
    """Get reservation by confirmation number."""
    return service.get_reservation(confirmation_number=confirmation_number)


@router.get(
    "",
    response_model=List[ReservationResponse],
    summary="Search reservations",
)
async def search_reservations(
    property_id: Optional[int] = Query(None, description="Filter by property"),
    guest_id: Optional[int] = Query(None, description="Filter by guest"),
    status: Optional[str] = Query(None, description="Reservation status"),
    check_in_date: Optional[date] = Query(None, description="Check-in date"),
    limit: int = Query(100, ge=1, le=1000),
    service: ReservationService = Depends(get_reservation_service),
):
    """
    # Search reservations using filters.
    """
    status_enum: Optional[ReservationStatus] = None

    if status:
        try:
            status_enum = ReservationStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid reservation status: {status}",
            )

    return service.search_reservations(
        property_id=property_id,
        guest_id=guest_id,
        status=status_enum,
        check_in_date=check_in_date,
        limit=limit,
    )


@router.put(
    "/{reservation_id}",
    response_model=ReservationResponse,
    summary="Update reservation",
)
async def update_reservation(
    reservation_id: int,
    data: ReservationUpdate,
    service: ReservationService = Depends(get_reservation_service),
    current_user: dict = Depends(get_current_user),
):
    """Update reservation details."""
    reservation = service.modify_reservation(
        reservation_id=reservation_id,
        check_in_date=data.check_in_date,
        check_out_date=data.check_out_date,
        num_adults=data.num_adults,
        num_children=data.num_children,
        special_requests=data.special_requests,
        modified_by=str(current_user.id) if hasattr(current_user, "id") else "system",
    )
    write_audit(service.db, "update_reservation", "reservation",
                current_user=current_user, resource_id=reservation_id)
    return reservation


@router.delete(
    "/{reservation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete reservation",
)
async def delete_reservation(
    reservation_id: int,
    service: ReservationService = Depends(get_reservation_service),
    current_user: dict = Depends(get_current_user),
):
    """Permanently delete a reservation. Cannot delete checked-in reservations."""
    try:
        service.delete_reservation(reservation_id=reservation_id)
    except BusinessRuleError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    write_audit(service.db, "delete_reservation", "reservation",
                current_user=current_user, resource_id=reservation_id)


@router.post(
    "/{reservation_id}/confirm",
    response_model=ReservationResponse,
    summary="Confirm reservation",
)
async def confirm_reservation(
    reservation_id: int,
    service: ReservationService = Depends(get_reservation_service),
    current_user: dict = Depends(get_current_user),
):
    """Confirm a pending reservation."""
    reservation = service.confirm_reservation(
        res_id=reservation_id,
        confirmed_by=str(current_user.id) if hasattr(current_user, "id") else "system",
    )
    write_audit(service.db, "confirm_reservation", "reservation",
                current_user=current_user, resource_id=reservation_id)
    return reservation


@router.post(
    "/{reservation_id}/cancel",
    response_model=ReservationResponse,
    summary="Cancel reservation",
)
async def cancel_reservation(
    reservation_id: int,
    reason: Optional[str] = Query(None, description="Cancellation reason"),
    force: bool = Query(False, description="Force cancellation"),
    service: ReservationService = Depends(get_reservation_service),
    current_user: dict = Depends(get_current_user),
):
    """Cancel a reservation."""
    try:
        reservation = service.cancel_reservation(
            reservation_id=reservation_id,
            cancelled_by=str(current_user.id)
            if hasattr(current_user, "id")
            else "system",
            reason=reason,
            force=force,
        )
    except BusinessRuleError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    write_audit(service.db, "cancel_reservation", "reservation",
                current_user=current_user, resource_id=reservation_id,
                details=reason)
    return reservation
