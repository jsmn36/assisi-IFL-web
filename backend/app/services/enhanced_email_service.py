from app.services.email_service import EmailService
from app.services.template_service import template_service
from app.services.notification_preference_service import NotificationPreferenceService
from typing import Dict
from sqlalchemy.orm import Session
import logging

# ✅ FIX: __name__ instead of name
logger = logging.getLogger(__name__)


class EnhancedEmailService(EmailService):
    """
    Enhanced email service with template rendering

    Extends EmailService to add template support
    """

    def __init__(self, db: Session = None):
        super().__init__()
        self.db = db

    def send_template_email(
        self,
        to_email: str,
        template_name: str,
        context: Dict,
        subject: str = None,
        user_id: int = None,
        notification_type: str = None,
    ) -> bool:
        """
        Send email using template
        """

        # ✅ Check notification preferences
        if user_id and notification_type and self.db:
            pref_service = NotificationPreferenceService(self.db)

            if not pref_service.should_send_notification(user_id, notification_type):
                logger.info(
                    f"Notification {notification_type} disabled for user {user_id}"
                )
                return False

        try:
            # ✅ Render HTML template
            html_body = template_service.render_template(
                f"{template_name}.html", context
            )

            # ✅ Render text template (safe fallback)
            try:
                text_body = template_service.render_text_template(
                    f"{template_name}.txt", context
                )
            except Exception:
                text_body = context.get(
                    "text_body", "Please view this email in HTML format."
                )

            # ✅ Subject fallback
            if not subject:
                subject = context.get("email_subject", "Assisi Social Notification")

            # ✅ Send email
            return self.send_email(
                to_email=to_email, subject=subject, body=text_body, html_body=html_body
            )

        except Exception as e:
            logger.error(f"Error sending template email: {e}", exc_info=True)
            return False

    def preview_template(self, template_name: str, context: Dict) -> Dict:
        """
        Preview template rendering
        """

        try:
            html = template_service.render_template(
                f"{template_name}.html",
                context,
                inline_css=False,  # ✅ Don't inline for preview
            )

            try:
                text = template_service.render_text_template(
                    f"{template_name}.txt", context
                )
            except Exception:
                text = "No text template available"

            return {"html": html, "text": text, "template_name": template_name}

        except Exception as e:
            logger.error(f"Error previewing template: {e}", exc_info=True)
            raise


# ✅ Helper class
class EmailTemplates:
    """Quick access to send common email templates"""

    @staticmethod
    def send_reservation_confirmation(
        db: Session, reservation_id: int, to_email: str
    ) -> bool:
        """Send reservation confirmation email"""

        from app.models import Reservation

        reservation = (
            db.query(Reservation).filter(Reservation.id == reservation_id).first()
        )

        if not reservation:
            return False

        context = {
            "guest_name": reservation.guest_name,
            "confirmation_code": reservation.confirmation_code,
            "check_in_date": reservation.check_in_date,
            "check_out_date": reservation.check_out_date,
            "room_type": getattr(reservation, "room_type", "Standard"),
            "number_of_guests": reservation.number_of_guests,
            "total_amount": reservation.total_amount or 0,
            "management_url": f"https://assisisocial.com/reservations/{reservation.id}",
        }

        service = EnhancedEmailService(db)

        return service.send_template_email(
            to_email=to_email,
            template_name="reservation_confirmation",
            context=context,
            subject=f"Reservation Confirmation - {reservation.confirmation_code}",
            notification_type="reservation_confirmation",
        )

    @staticmethod
    def send_checkin_reminder(db: Session, reservation_id: int, to_email: str) -> bool:
        """Send check-in reminder email"""

        from app.models import Reservation

        reservation = (
            db.query(Reservation).filter(Reservation.id == reservation_id).first()
        )

        if not reservation:
            return False

        context = {
            "guest_name": reservation.guest_name,
            "confirmation_code": reservation.confirmation_code,
            "check_in_date": reservation.check_in_date,
            "room_type": getattr(reservation, "room_type", "Standard"),
            "management_url": f"https://assisisocial.com/reservations/{reservation.id}",
        }

        service = EnhancedEmailService(db)

        return service.send_template_email(
            to_email=to_email,
            template_name="checkin_reminder",
            context=context,
            subject=f"Check-in Reminder - {reservation.confirmation_code}",
            notification_type="reservation_reminder",
        )
