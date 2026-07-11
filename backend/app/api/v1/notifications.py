from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import Optional
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, get_current_user
from app.services.notification_service import NotificationService
from app.models.reservation import Reservation
from app.models.stay import Stay
from app.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def _get_email_task(task_name: str):
    """Lazy-load celery email tasks only in PostgreSQL mode."""
    if settings.is_postgresql_mode:
        from app.tasks.email_tasks import (
            send_reservation_confirmation_email,
            send_check_in_reminder_email,
            send_checkout_receipt_email,
        )

        tasks = {
            "confirmation": send_reservation_confirmation_email,
            "reminder": send_check_in_reminder_email,
            "receipt": send_checkout_receipt_email,
        }
        return tasks.get(task_name)
    return None


@router.post(
    "/reservation/{reservation_id}/confirmation",
    summary="Send reservation confirmation email",
    status_code=status.HTTP_202_ACCEPTED,
)
async def send_confirmation(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """Send reservation confirmation email (queued via Celery or inline)"""
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found",
        )

    task_fn = _get_email_task("confirmation")
    if task_fn:
        try:
            task = task_fn.delay(reservation_id)
            return {
                "message": "Confirmation email queued",
                "task_id": task.id,
                "reservation_id": reservation_id,
            }
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Email queue unavailable",
            )
    else:
        logger.info(
            "SQLite mode: email task skipped for reservation %s", reservation_id
        )
        return {
            "message": "Confirmation email skipped (SQLite mode)",
            "task_id": None,
            "reservation_id": reservation_id,
        }


@router.post(
    "/reservation/{reservation_id}/reminder",
    summary="Send check-in reminder email",
    status_code=status.HTTP_202_ACCEPTED,
)
async def send_reminder(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """Send check-in reminder email (queued via Celery or inline)"""
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found",
        )

    task_fn = _get_email_task("reminder")
    if task_fn:
        try:
            task = task_fn.delay(reservation_id)
            return {
                "message": "Check-in reminder queued",
                "task_id": task.id,
                "reservation_id": reservation_id,
            }
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Email queue unavailable",
            )
    else:
        logger.info("SQLite mode: reminder skipped for reservation %s", reservation_id)
        return {
            "message": "Check-in reminder skipped (SQLite mode)",
            "task_id": None,
            "reservation_id": reservation_id,
        }


@router.post(
    "/stay/{stay_id}/receipt",
    summary="Send checkout receipt email",
    status_code=status.HTTP_202_ACCEPTED,
)
async def send_receipt(
    stay_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """Send checkout receipt email (queued via Celery or inline)"""
    stay = db.query(Stay).filter(Stay.id == stay_id).first()
    if not stay:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stay not found",
        )

    task_fn = _get_email_task("receipt")
    if task_fn:
        try:
            task = task_fn.delay(stay_id)
            return {
                "message": "Checkout receipt queued",
                "task_id": task.id,
                "stay_id": stay_id,
            }
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Email queue unavailable",
            )
    else:
        logger.info("SQLite mode: receipt skipped for stay %s", stay_id)
        return {
            "message": "Checkout receipt skipped (SQLite mode)",
            "task_id": None,
            "stay_id": stay_id,
        }


@router.get(
    "/history",
    summary="Get notification history",
)
async def get_notification_history(
    guest_id: Optional[int] = Query(None),
    reservation_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """Get notification history with optional filtering"""
    service = NotificationService(db)
    notifications = service.get_notification_history(guest_id, reservation_id, limit)

    return {
        "notifications": [
            {
                "id": n.id,
                "type": n.type.value,
                "status": n.status.value,
                "recipient": n.recipient_email,
                "subject": n.subject,
                "sent_at": n.sent_at.isoformat() if n.sent_at else None,
                "created_at": n.created_at.isoformat(),
            }
            for n in notifications
        ],
        "total": len(notifications),
    }


@router.get(
    "/guest/{guest_id}/history",
    summary="Get guest notification history",
)
async def get_guest_notifications(
    guest_id: int,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """Get all notifications for a specific guest"""
    service = NotificationService(db)
    notifications = service.get_notification_history(guest_id=guest_id, limit=limit)

    return {
        "guest_id": guest_id,
        "notifications": [
            {
                "id": n.id,
                "type": n.type.value,
                "status": n.status.value,
                "recipient": n.recipient_email,
                "subject": n.subject,
                "sent_at": n.sent_at.isoformat() if n.sent_at else None,
                "created_at": n.created_at.isoformat(),
            }
            for n in notifications
        ],
        "total": len(notifications),
    }
