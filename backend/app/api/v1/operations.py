"""
# Operations API Endpoints
Check-in and Check-out workflows
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.dependencies import (
    get_check_in_service,
    get_check_out_service,
    get_current_user,
    get_db,
)
from app.api.schemas import (
    CheckInRequest,
    CheckInResponse,
    CheckOutRequest,
    CheckOutResponse,
    ReservationResponse,
)
from app.services import CheckInService, CheckOutService
from app.services.base_service import BusinessRuleError, NotFoundError

router = APIRouter(prefix="/operations", tags=["Operations"])


@router.post(
    "/check-in",
    response_model=CheckInResponse,
    status_code=status.HTTP_200_OK,
    summary="Check in guest",
)
async def check_in(
    data: CheckInRequest,
    service: CheckInService = Depends(get_check_in_service),
    current_user: dict = Depends(get_current_user),
):
    try:
        result = service.check_in(
            reservation_id=data.reservation_id,
            confirmation_number=data.confirmation_number,
            room_id=data.room_id,
            room_number=data.room_number,
            checked_in_by=str(current_user.id)
            if hasattr(current_user, "id")
            else "system",
            post_room_charges=data.post_room_charges,
        )
    except (BusinessRuleError, NotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    stay = result.get("stay")
    return CheckInResponse(
        success=result["success"],
        message=result["message"],
        reservation=ReservationResponse.from_orm(result["reservation"]),
        room_number=result["room"].room_number,
        charges_posted=result["charges_posted"],
        warnings=result["warnings"],
        stay_id=stay.id if stay else None,
    )


@router.post(
    "/check-out",
    response_model=CheckOutResponse,
    status_code=status.HTTP_200_OK,
    summary="Check out guest",
)
async def check_out(
    data: CheckOutRequest,
    service: CheckOutService = Depends(get_check_out_service),
    current_user: dict = Depends(get_current_user),
):
    try:
        result = service.check_out(
            stay_id=data.stay_id,
            reservation_id=data.reservation_id,
            room_id=data.room_id,
            checked_out_by=str(current_user.id)
            if hasattr(current_user, "id")
            else "system",
            payment_method=data.payment_method,
            force_checkout=data.force_checkout,
        )
    except (BusinessRuleError, NotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    return CheckOutResponse(
        success=result["success"],
        message=result["message"],
        bill=result["bill"],
        payment=result["payment"],
        warnings=result["warnings"],
    )


@router.post(
    "/check-out/preview",
    status_code=status.HTTP_200_OK,
    summary="Preview check-out bill",
)
async def preview_check_out(
    data: CheckOutRequest, service: CheckOutService = Depends(get_check_out_service)
):
    from app.models import Stay

    try:
        if data.stay_id:
            stay = service.stay_service.get_stay(data.stay_id)
        elif data.reservation_id:
            stay = (
                service.db.query(Stay)
                .filter(
                    Stay.reservation_id == data.reservation_id,
                    Stay.status == "checked_in",
                )
                .first()
            )
            if not stay:
                raise BusinessRuleError("No active stay found for reservation")
        else:
            raise BusinessRuleError("Provide stay or reservation id")

        if not stay:
            raise BusinessRuleError("Stay not found")

        bill = service.get_final_bill(stay.id)
        return {"success": True, "bill": bill, "warnings": []}
    except (BusinessRuleError, NotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )


@router.get(
    "/daily-summary/{property_id}",
    status_code=status.HTTP_200_OK,
    summary="Get daily operations summary",
)
async def get_daily_summary_endpoint(
    property_id: int, date: str = Query(...), db=Depends(get_db)
):
    from datetime import datetime
    from app.services.workflow_automation_service import WorkflowAutomationService

    target_date = datetime.strptime(date, "%Y-%m-%d").date()
    service = WorkflowAutomationService(db)
    return service.get_daily_summary(property_id, target_date)


@router.post(
    "/daily-housekeeping/{property_id}",
    status_code=status.HTTP_200_OK,
    summary="Run daily housekeeping automation",
)
async def run_daily_housekeeping_endpoint(
    property_id: int,
    date: str = Query(None),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    from datetime import datetime, date as date_obj
    from app.services.workflow_automation_service import WorkflowAutomationService

    target_date = (
        datetime.strptime(date, "%Y-%m-%d").date() if date else date_obj.today()
    )
    created_by = str(current_user.id) if hasattr(current_user, "id") else "system"

    service = WorkflowAutomationService(db)
    result = service.process_daily_housekeeping(property_id, target_date, created_by)
    return {"success": True, "total": result.get("total", 0)}
