from app.config import settings

if not settings.is_postgresql_mode:
    raise ImportError(
        "Celery tasks require PostgreSQL mode. Set DATABASE_URL to enable."
    )

from celery import shared_task
from app.tasks.base import RetryTask
from app.services.enhanced_email_service import EmailTemplates
import logging

logger = logging.getLogger(__name__)  # ✅ FIXED


@shared_task(bind=True, base=RetryTask, queue="emails")
def send_template_confirmation_email(self, reservation_id: int):
    """
    Send reservation confirmation using template

    Uses: reservation_confirmation.html template
    """
    from app.database import SessionLocal
    from app.models import Reservation

    db = SessionLocal()

    try:
        reservation = (
            db.query(Reservation).filter(Reservation.id == reservation_id).first()
        )

        if not reservation:
            logger.error(f"Reservation {reservation_id} not found")
            return {"success": False, "error": "Reservation not found"}

        success = EmailTemplates.send_reservation_confirmation(
            db=db,
            reservation_id=reservation_id,
            to_email=reservation.guest_email,
        )

        return {
            "success": success,
            "reservation_id": reservation_id,
            "email": reservation.guest_email,
            "template": "reservation_confirmation",
        }

    except Exception as e:
        logger.exception(
            f"Failed to send confirmation email for reservation {reservation_id}"
        )
        raise self.retry(exc=e)

    finally:
        db.close()


@shared_task(bind=True, base=RetryTask, queue="emails")
def send_template_reminder_email(self, reservation_id: int, reminder_type: str):
    """
    Send reminder email using template

    Types: check_in, check_out
    """
    from app.database import SessionLocal
    from app.models import Reservation

    db = SessionLocal()

    try:
        reservation = (
            db.query(Reservation).filter(Reservation.id == reservation_id).first()
        )

        if not reservation:
            logger.error(f"Reservation {reservation_id} not found")
            return {"success": False, "error": "Reservation not found"}

        success = False

        if reminder_type == "check_in":
            success = EmailTemplates.send_checkin_reminder(
                db=db,
                reservation_id=reservation_id,
                to_email=reservation.guest_email,
            )

        elif reminder_type == "check_out":
            # TODO: Implement this properly
            logger.warning("Checkout reminder not implemented yet")
            success = False

        else:
            logger.error(f"Invalid reminder type: {reminder_type}")
            return {
                "success": False,
                "error": "Invalid reminder type",
            }

        return {
            "success": success,
            "reservation_id": reservation_id,
            "reminder_type": reminder_type,
            "template": f"{reminder_type}_reminder",
        }

    except Exception as e:
        logger.exception(
            f"Failed to send {reminder_type} reminder for reservation {reservation_id}"
        )
        raise self.retry(exc=e)

    finally:
        db.close()
