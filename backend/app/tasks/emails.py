from app.config import settings

if not settings.is_postgresql_mode:
    raise ImportError(
        "Celery tasks require PostgreSQL mode. " "Set DATABASE_URL to enable."
    )

from celery import shared_task
from app.tasks.base import RetryTask
from app.services.email_service import EmailService
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, base=RetryTask, queue="emails")
def send_confirmation_email(self, reservation_id: int):
    """
    Send reservation confirmation email
    """
    from app.models import Reservation
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        reservation = (
            db.query(Reservation).filter(Reservation.id == reservation_id).first()
        )

        if not reservation:
            logger.error(f"Reservation {reservation_id} not found")
            return {"success": False, "error": "Reservation not found"}

        email_service = EmailService()

        subject = f"Reservation Confirmation - {reservation.confirmation_code}"

        body = f"""
Dear {reservation.guest_name},

Thank you for your reservation!

Confirmation Number: {reservation.confirmation_code}
Check-in Date: {reservation.check_in_date}
Check-out Date: {reservation.check_out_date}
Room Type: {getattr(reservation, 'room_type', 'Standard')}
Number of Guests: {reservation.number_of_guests}

We look forward to welcoming you!

Best regards,
Assisi Social Team
"""

        html_body = f"""
<h2>Reservation Confirmation</h2>

<p>Dear {reservation.guest_name},</p>

<p>Thank you for your reservation!</p>

<table style="margin: 20px 0; border-collapse: collapse;">
    <tr>
        <td><b>Confirmation Number:</b></td>
        <td>{reservation.confirmation_code}</td>
    </tr>
    <tr>
        <td><b>Check-in Date:</b></td>
        <td>{reservation.check_in_date}</td>
    </tr>
    <tr>
        <td><b>Check-out Date:</b></td>
        <td>{reservation.check_out_date}</td>
    </tr>
    <tr>
        <td><b>Guests:</b></td>
        <td>{reservation.number_of_guests}</td>
    </tr>
</table>

<p>We look forward to welcoming you!</p>
<p>Best regards,<br>Assisi Social Team</p>
"""

        success = email_service.send_email(
            to_email=reservation.guest_email,
            subject=subject,
            body=body,
            html_body=html_body,
        )

        return {
            "success": success,
            "reservation_id": reservation_id,
            "email": reservation.guest_email,
            "sent_at": datetime.now(timezone.utc).isoformat(),
        }

    finally:
        db.close()


@shared_task(bind=True, base=RetryTask, queue="emails")
def send_reminder_email(self, reservation_id: int, reminder_type: str):
    """
    Send reminder email
    """
    from app.models import Reservation
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        reservation = (
            db.query(Reservation).filter(Reservation.id == reservation_id).first()
        )

        if not reservation:
            return {"success": False, "error": "Reservation not found"}

        email_service = EmailService()

        if reminder_type == "check_in":
            subject = f"Check-in Reminder - {reservation.confirmation_code}"
            body = f"""
Dear {reservation.guest_name},

This is a reminder that your check-in is tomorrow!

Confirmation Number: {reservation.confirmation_code}
Check-in Date: {reservation.check_in_date}
Check-in Time: 3:00 PM

See you soon!
Assisi Social Team
"""

        elif reminder_type == "check_out":
            subject = f"Check-out Reminder - {reservation.confirmation_code}"
            body = f"""
Dear {reservation.guest_name},

This is a reminder that your check-out is tomorrow.

Confirmation Number: {reservation.confirmation_code}
Check-out Date: {reservation.check_out_date}
Check-out Time: 11:00 AM

Thank you for staying with us!
Assisi Social Team
"""

        else:
            subject = f"Reservation Reminder - {reservation.confirmation_code}"
            body = f"""
Dear {reservation.guest_name},

This is a reminder regarding your reservation.

Confirmation Number: {reservation.confirmation_code}

Assisi Social Team
"""

        success = email_service.send_email(
            to_email=reservation.guest_email, subject=subject, body=body
        )

        return {
            "success": success,
            "reservation_id": reservation_id,
            "reminder_type": reminder_type,
        }

    finally:
        db.close()


@shared_task(bind=True, base=RetryTask, queue="emails")
def send_bulk_notification(self, email_list: list, subject: str, body: str):
    """
    Send bulk email notification
    """
    email_service = EmailService()

    results = email_service.send_bulk_email(
        recipients=email_list, subject=subject, body=body
    )

    logger.info(f"Bulk email sent: {results['sent']}/{results['total']}")

    return results
