from fastapi import APIRouter, Depends, Query, status
from typing import Optional, List
from datetime import date
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user
from app.services import HousekeepingService, MaintenanceService
from app.models import TaskStatus, TaskPriority, User

from app.schemas import (
    CreateTaskRequest,
    CreateMaintenanceRequest,
    CompleteMaintenanceRequest,
    HousekeepingStaffOut,
    HousekeepingStaffCreate,
)

router = APIRouter(prefix="/housekeeping", tags=["Housekeeping & Maintenance"])


# =========================
# Housekeeping Tasks
# =========================


@router.post("/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: CreateTaskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = HousekeepingService(db)
    return service.create_task(**payload.dict(), created_by=current_user.username)


@router.get("/tasks")
async def get_tasks(
    property_id: int = Query(...),
    target_date: Optional[date] = Query(None),
    status: Optional[TaskStatus] = Query(None),
    db: Session = Depends(get_db),
):
    service = HousekeepingService(db)

    tasks = (
        service.get_tasks_by_date(property_id, target_date, status)
        if target_date
        else service.get_pending_tasks(property_id)
    )

    return {"tasks": tasks, "total": len(tasks)}


@router.post("/tasks/{task_id}/assign")
async def assign_task(
    task_id: int,
    staff_user_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = HousekeepingService(db)
    return service.assign_task(task_id, staff_user_id, current_user.username)


@router.post("/tasks/{task_id}/start")
async def start_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = HousekeepingService(db)
    return service.start_task(task_id, current_user.username)


@router.post("/tasks/{task_id}/complete")
async def complete_task(
    task_id: int,
    notes: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = HousekeepingService(db)
    return service.complete_task(task_id, notes, current_user.username)


@router.post("/tasks/{task_id}/inspect")
async def inspect_task(
    task_id: int,
    passed: bool = Query(...),
    inspector_user_id: int = Query(...),
    notes: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    service = HousekeepingService(db)
    return service.inspect_task(task_id, passed, inspector_user_id, notes)


@router.post("/tasks/auto-assign")
async def auto_assign_tasks(
    property_id: int = Query(...),
    target_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = HousekeepingService(db)
    return service.auto_assign_tasks(property_id, target_date, current_user.username)


@router.post("/tasks/create-checkout-tasks")
async def create_checkout_tasks(
    property_id: int = Query(...),
    checkout_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = HousekeepingService(db)
    tasks = service.create_checkout_tasks(
        property_id, checkout_date, current_user.username
    )
    return {"tasks": tasks, "total": len(tasks)}


# =========================
# Maintenance Requests
# =========================


@router.post("/maintenance", status_code=status.HTTP_201_CREATED)
async def create_maintenance_request(
    payload: CreateMaintenanceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = MaintenanceService(db)
    return service.create_request(
        **payload.dict(exclude={"created_by"}), created_by=current_user.username
    )


@router.get("/maintenance")
async def get_maintenance_requests(
    property_id: int = Query(...),
    category: Optional[str] = Query(None),
    priority: Optional[TaskPriority] = Query(None),
    db: Session = Depends(get_db),
):
    service = MaintenanceService(db)
    requests = service.get_active_requests(property_id, category, priority)
    return {"requests": requests, "total": len(requests)}


@router.get("/maintenance/overdue")
async def get_overdue_requests(
    property_id: int = Query(...), db: Session = Depends(get_db)
):
    service = MaintenanceService(db)
    requests = service.get_overdue_requests(property_id)
    return {"requests": requests, "total": len(requests)}


@router.get("/maintenance/stats")
async def get_maintenance_stats(
    property_id: int = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
):
    service = MaintenanceService(db)
    return service.get_request_stats(property_id, start_date, end_date)


@router.post("/maintenance/{request_id}/assign")
async def assign_maintenance_request(
    request_id: int,
    technician_user_id: int = Query(...),
    scheduled_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = MaintenanceService(db)
    return service.assign_request(
        request_id, technician_user_id, scheduled_date, current_user.username
    )


@router.post("/maintenance/{request_id}/start")
async def start_maintenance_work(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = MaintenanceService(db)
    return service.start_work(request_id, current_user.username)


@router.post("/maintenance/{request_id}/complete")
async def complete_maintenance_work(
    request_id: int,
    payload: CompleteMaintenanceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = MaintenanceService(db)
    return service.complete_work(
        request_id, payload.resolution_notes, payload.actual_cost, current_user.username
    )


@router.post("/maintenance/{request_id}/close")
async def close_maintenance_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = MaintenanceService(db)
    return service.close_request(request_id, current_user.username)


# =========================
# Housekeeping Staff
# =========================


@router.get("/staff", response_model=List[HousekeepingStaffOut])
async def get_staff(
    property_id: int = Query(...),
    db: Session = Depends(get_db),
):
    service = HousekeepingService(db)
    return service.get_staff(property_id)


@router.post("/staff", response_model=HousekeepingStaffOut)
async def create_staff(
    payload: HousekeepingStaffCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = HousekeepingService(db)
    return service.create_staff_member(
        payload.property_id, payload.user_id, payload.role
    )


@router.post("/staff/{staff_id}/deactivate", response_model=HousekeepingStaffOut)
async def deactivate_staff(
    staff_id: int,
    db: Session = Depends(get_db),
):
    service = HousekeepingService(db)
    return service.update_staff_member(staff_id, is_active=False)
