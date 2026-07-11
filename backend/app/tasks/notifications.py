from app.config import settings

if not settings.is_postgresql_mode:
    raise ImportError(
        "Celery tasks require PostgreSQL mode. Set DATABASE_URL to enable."
    )

from celery import shared_task
from app.tasks.base import DatabaseTask
from datetime import datetime, timedelta, date, timezone
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, base=DatabaseTask, queue="notifications")
def check_reservation_reminders(self):
    """
    Check for upcoming reservations and send reminders

    Runs every 30 minutes (configured in beat_schedule)
    """
    from app.models import Reservation
    from app.tasks.emails import send_reminder_email

    logger.info("Checking reservation reminders")

    tomorrow = date.today() + timedelta(days=1)

    try:
        # Check-in reminders (1 day before)
        checkin_reservations = (
            self.db.query(Reservation)
            .filter(
                Reservation.check_in_date == tomorrow, Reservation.status == "confirmed"
            )
            .all()
        )

        for reservation in checkin_reservations:
            send_reminder_email.delay(reservation.id, "check_in")

        # Check-out reminders (1 day before)
        checkout_reservations = (
            self.db.query(Reservation)
            .filter(
                Reservation.check_out_date == tomorrow,
                Reservation.status == "checked_in",
            )
            .all()
        )

        for reservation in checkout_reservations:
            send_reminder_email.delay(reservation.id, "check_out")

        return {
            "checkin_reminders": len(checkin_reservations),
            "checkout_reminders": len(checkout_reservations),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.exception("Error checking reservation reminders")
        raise e


@shared_task(bind=True, base=DatabaseTask, queue="notifications")
def notify_housekeeping_tasks(self):
    """Notify housekeeping staff of pending tasks"""
    from app.models import HousekeepingTask

    try:
        pending_tasks = (
            self.db.query(HousekeepingTask)
            .filter(
                HousekeepingTask.status == "pending",
                HousekeepingTask.scheduled_date == date.today(),
            )
            .count()
        )

        logger.info(f"Pending housekeeping tasks: {pending_tasks}")

        # Future: send notifications here

        return {
            "pending_tasks": pending_tasks,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.exception("Error notifying housekeeping tasks")
        raise e
