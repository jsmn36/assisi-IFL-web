"""
Celery Email Tasks
Background tasks for sending email notifications — requires PostgreSQL mode.
"""
from app.config import settings

if not settings.is_postgresql_mode:
    raise ImportError(
        "Celery tasks require PostgreSQL mode. Set DATABASE_URL to enable."
    )

from celery import Task
from datetime import date, timedelta
from typing import Dict, Any, Optional
import logging
import asyncio
import concurrent.futures

from app.core.celery_app import celery_app
from app.database import SessionLocal
from app.services.notification_service import NotificationService
from app.models import Reservation, Notification, NotificationType
from sqlalchemy.orm import Session  # FIX 1: Import Session for correct type hint

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task with database session management"""

    _db: Optional[
        Session
    ] = None  # FIX 1: Session is the correct type, not SessionLocal

    @property
    def db(self):
        """Lazy-loaded database session"""
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        """Clean up database session after task completes"""
        if self._db is not None:
            try:
                self._db.close()
            except Exception as e:
                logger.warning(f"Error closing DB session: {e}")
            finally:
                self._db = None


def run_async_in_loop(coro):
    """
    Run coroutine in event loop safely.
    Handles both new loop creation and existing loop cases.
    """
    # FIX 2: Restructured to avoid double-execution bug.
    # If a loop is already running (e.g. in tests), use a thread to run a fresh loop.
    # Otherwise, create and run a new loop directly.
    try:
        asyncio.get_running_loop()
        # A loop is running — spin up a thread with its own event loop
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()
    except RuntimeError:
        # No loop running — safe to create one directly
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(coro)
        finally:
            loop.close()
            asyncio.set_event_loop(None)


@celery_app.task(
    base=DatabaseTask,
    bind=True,
    name="app.tasks.email_tasks.send_reservation_confirmation_email",
    max_retries=3,
    default_retry_delay=60,
)
def send_reservation_confirmation_email(self, reservation_id: int) -> Dict[str, Any]:
    """
    Send reservation confirmation email (background task)

    Args:
        reservation_id: Reservation ID

    Returns:
        Dict with notification_id and status
    """
    try:
        logger.info(f"Sending confirmation email for reservation {reservation_id}")

        notification_service = NotificationService(self.db)

        notification = run_async_in_loop(
            notification_service.send_reservation_confirmation(reservation_id)
        )

        logger.info(f"Confirmation email sent: {notification.id}")
        return {"notification_id": notification.id, "status": notification.status.value}

    except Exception as exc:
        logger.error(f"Failed to send confirmation email: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(
    base=DatabaseTask,
    bind=True,
    name="app.tasks.email_tasks.send_check_in_reminder_email",
    max_retries=3,
    default_retry_delay=60,
)
def send_check_in_reminder_email(self, reservation_id: int) -> Dict[str, Any]:
    """
    Send check-in reminder email (background task)

    Args:
        reservation_id: Reservation ID

    Returns:
        Dict with notification_id and status
    """
    try:
        logger.info(f"Sending check-in reminder for reservation {reservation_id}")

        notification_service = NotificationService(self.db)

        notification = run_async_in_loop(
            notification_service.send_check_in_reminder(reservation_id)
        )

        logger.info(f"Check-in reminder sent: {notification.id}")
        return {"notification_id": notification.id, "status": notification.status.value}

    except Exception as exc:
        logger.error(f"Failed to send check-in reminder: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(
    base=DatabaseTask,
    bind=True,
    name="app.tasks.email_tasks.send_checkout_receipt_email",
    max_retries=3,
    default_retry_delay=60,
)
def send_checkout_receipt_email(self, stay_id: int) -> Dict[str, Any]:
    """
    Send checkout receipt email (background task)

    Args:
        stay_id: Stay ID

    Returns:
        Dict with notification_id and status
    """
    try:
        logger.info(f"Sending checkout receipt for stay {stay_id}")

        notification_service = NotificationService(self.db)

        notification = run_async_in_loop(
            notification_service.send_checkout_receipt(stay_id)
        )

        logger.info(f"Checkout receipt sent: {notification.id}")
        return {"notification_id": notification.id, "status": notification.status.value}

    except Exception as exc:
        logger.error(f"Failed to send checkout receipt: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(
    base=DatabaseTask,
    bind=True,
    name="app.tasks.email_tasks.send_check_in_reminders",
    max_retries=1,
)
def send_check_in_reminders(self) -> Dict[str, Any]:
    """
    Send check-in reminders for tomorrow's arrivals (periodic task)

    Finds all confirmed reservations checking in tomorrow and queues
    reminder emails for guests who haven't received one yet.
    """
    try:
        logger.info("Running check-in reminder task")

        tomorrow = date.today() + timedelta(days=1)

        reservations = (
            self.db.query(Reservation)
            .filter(
                Reservation.status == "confirmed", Reservation.check_in_date == tomorrow
            )
            .all()
        )

        logger.info(f"Found {len(reservations)} reservations for tomorrow")

        sent_count = 0
        for reservation in reservations:
            # Check if reminder already sent
            existing = (
                self.db.query(Notification)
                .filter(
                    Notification.reservation_id == reservation.id,
                    Notification.template_name == "check_in_reminder",
                    Notification.type == NotificationType.EMAIL,
                )
                .first()
            )

            if existing:
                logger.info(f"Reminder already sent for reservation {reservation.id}")
                continue

            # Queue individual reminder task
            send_check_in_reminder_email.delay(reservation.id)
            sent_count += 1

        logger.info(f"Queued {sent_count} check-in reminders")
        return {"sent": sent_count, "total": len(reservations)}

    except Exception as exc:
        logger.error(f"Failed to send check-in reminders: {exc}")
        raise self.retry(exc=exc)
