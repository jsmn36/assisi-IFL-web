"""
Task Monitoring API
Monitor and analyze background tasks
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, require_role
from app.services.task_monitoring_service import TaskMonitoringService
from app.models import User
from typing import Optional

router = APIRouter(prefix="/task-monitoring", tags=["Task Monitoring"])


@router.get("/history")
async def get_task_history(
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    """Get recent task history"""
    service = TaskMonitoringService(db)
    tasks = service.get_recent_tasks(limit=limit, status=status)
    return {
        "tasks": [
            {
                "task_id": t.task_id,
                "task_name": t.task_name,
                "status": t.status,
                "started_at": t.started_at.isoformat() if t.started_at else None,
                "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                "duration_seconds": t.duration_seconds,
                "queue_name": t.queue_name,
                "retries": t.retries,
            }
            for t in tasks
        ],
        "total": len(tasks),
    }


@router.get("/statistics")
async def get_task_statistics(
    hours: int = Query(24, ge=1, le=168),
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    """Get task statistics for the last N hours (max 168 = 7 days)"""
    service = TaskMonitoringService(db)
    return service.get_task_statistics(hours=hours)


@router.get("/failed")
async def get_failed_tasks(
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Get recent failed tasks (admin only)"""
    service = TaskMonitoringService(db)
    failed = service.get_failed_tasks(limit=limit)
    return {
        "failed_tasks": [
            {
                "task_id": t.task_id,
                "task_name": t.task_name,
                "error": t.error,
                "started_at": t.started_at.isoformat() if t.started_at else None,
                "retries": t.retries,
                "queue_name": t.queue_name,
            }
            for t in failed
        ],
        "total": len(failed),
    }


@router.get("/{task_id}")
async def get_task_details(
    task_id: str,
    current_user: User = Depends(
        require_role("admin", "manager", "accountant", "front_desk")
    ),
    db: Session = Depends(get_db),
):
    """Get full details for a specific task"""
    service = TaskMonitoringService(db)
    task = service.get_task_history(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "task_id": task.task_id,
        "task_name": task.task_name,
        "status": task.status,
        "result": task.result,
        "error": task.error,
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "duration_seconds": task.duration_seconds,
        "worker_name": task.worker_name,
        "queue_name": task.queue_name,
        "retries": task.retries,
        "max_retries": task.max_retries,
    }
