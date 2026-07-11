from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import json
import logging

from app.services.base_service import BaseService
from app.models import (
    Notification,
    NotificationType,
    NotificationStatus,
    Reservation,
    Stay,
    Guest,
)
from app.core.email.email_service import email_service
from app.core.email.template_renderer import template_renderer

logger = logging.getLogger(__name__)


class NotificationService(BaseService):
    """
    Service for managing notifications (email, SMS, push, in-app)

    Methods:
        send_reservation_confirmation: Send confirmation email
        send_check_in_reminder: Send reminder email
        send_checkout_receipt: Send receipt email
        send_email_notification: Generic email sender
        get_notification_history: Get notification logs
        retry_failed_notification: Retry a failed notification
    """

    def __init__(self, db: Session):
        super().__init__(db)
        self.db = db

    async def _send_notification_email(
        self, notification: Notification, html_content: str
    ) -> Notification:
        """
        Helper method to send email and update notification status.
        Handles success/failure logic in one place.

        Args:
            notification: Notification record to update
            html_content: HTML email content

        Returns:
            Updated notification record
        """
        if notification.status == NotificationStatus.SUPPRESSED:
            logger.info(
                "Skipping send for suppressed notification id=%s", notification.id
            )
            return notification
        try:
            success = await email_service.send_email(
                to_email=notification.recipient_email,
                subject=notification.subject,
                html_content=html_content,
                notification_id=notification.id,  # For tracking/logging
            )

            if success:
                notification.status = NotificationStatus.SENT
                notification.sent_at = datetime.now(timezone.utc)
                notification.error_message = None
                notification.retry_count = 0
                logger.info(
                    f"Email sent successfully: notification_id={notification.id}"
                )
            else:
                notification.status = NotificationStatus.FAILED
                notification.error_message = "Email service returned failure"
                notification.retry_count += 1
                logger.warning(
                    f"Email failed to send: notification_id={notification.id}"
                )

        except Exception as e:
            notification.status = NotificationStatus.FAILED
            notification.error_message = str(e)[:500]  # Limit error message length
            notification.retry_count += 1
            logger.error(
                f"Exception sending email: notification_id={notification.id}, error={e}"
            )

        self.commit()
        self.refresh(notification)
        return notification

    def _create_email_notification(
        self,
        recipient_email: str,
        guest_id: Optional[int],
        subject: str,
        template_name: str,
        template_data: Dict[str, Any],
        html_content: str,
        reservation_id: Optional[int] = None,
        stay_id: Optional[int] = None,
    ) -> Notification:
        """
        Helper to create notification record with consistent fields.

        Args:
            recipient_email: Target email address
            guest_id: Associated guest ID
            subject: Email subject
            template_name: Template identifier
            template_data: Data used for template rendering
            html_content: Rendered HTML content (stored as message)
            reservation_id: Optional reservation ID
            stay_id: Optional stay ID

        Returns:
            Created Notification record
        """
        # Suppression check — recipients on the suppression list never receive
        # mail. We still record the notification (as SUPPRESSED) so the
        # operator can see what was attempted.
        from app.services.suppression_service import SuppressionService
        from app.models.suppression import SuppressionChannel

        suppression = SuppressionService(self.db).is_suppressed(
            recipient_email, SuppressionChannel.EMAIL
        )

        notification = Notification(
            type=NotificationType.EMAIL,
            status=(
                NotificationStatus.SUPPRESSED
                if suppression
                else NotificationStatus.PENDING
            ),
            recipient_email=recipient_email,
            guest_id=guest_id,
            reservation_id=reservation_id,
            stay_id=stay_id,
            subject=subject,
            message=html_content,  # Store rendered content
            template_name=template_name,
            template_data=json.dumps(template_data, default=str),
            error_message=(
                f"suppressed:{suppression.reason.value}" if suppression else None
            ),
        )

        self.db.add(notification)
        self.commit()
        self.refresh(notification)
        return notification

    async def send_reservation_confirmation(self, reservation_id: int) -> Notification:
        """
        Send reservation confirmation email to guest.

        Args:
            reservation_id: Reservation ID

        Returns:
            Notification record

        Raises:
            ValueError: If guest has no email address
        """
        reservation = self.get_or_404(Reservation, reservation_id)
        guest = reservation.guest

        if not guest.email:
            raise ValueError(f"Guest {guest.id} has no email address")

        template_data = {
            "confirmation_number": reservation.confirmation_number,
            "guest_name": guest.full_name,
            "check_in_date": reservation.check_in_date,
            "check_out_date": reservation.check_out_date,
            "room_type": reservation.room_type.name,
            "num_nights": reservation.number_of_nights,
            "num_adults": reservation.num_adults,
            "num_children": reservation.num_children,
            "total_amount": float(reservation.total_amount),
        }

        html_content = template_renderer.render_reservation_confirmation(
            **template_data
        )

        notification = self._create_email_notification(
            recipient_email=guest.email,
            guest_id=guest.id,
            subject=f"Reservation Confirmed - {reservation.confirmation_number}",
            template_name="reservation_confirmation",
            template_data=template_data,
            html_content=html_content,
            reservation_id=reservation.id,
        )

        return await self._send_notification_email(notification, html_content)

    async def send_check_in_reminder(
        self, reservation_id: int, days_before: int = 1
    ) -> Notification:
        """
        Send check-in reminder email to guest.

        Args:
            reservation_id: Reservation ID
            days_before: Days before check-in (for template context)

        Returns:
            Notification record

        Raises:
            ValueError: If guest has no email address
        """
        reservation = self.get_or_404(Reservation, reservation_id)
        guest = reservation.guest

        if not guest.email:
            raise ValueError(f"Guest {guest.id} has no email address")

        template_data = {
            "guest_name": guest.full_name,
            "confirmation_number": reservation.confirmation_number,
            "check_in_date": reservation.check_in_date,
            "room_type": reservation.room_type.name,
            "days_before": days_before,
        }

        html_content = template_renderer.render_check_in_reminder(**template_data)

        notification = self._create_email_notification(
            recipient_email=guest.email,
            guest_id=guest.id,
            subject=f"Check-in Reminder - {reservation.confirmation_number}",
            template_name="check_in_reminder",
            template_data=template_data,
            html_content=html_content,
            reservation_id=reservation.id,
        )

        return await self._send_notification_email(notification, html_content)

    async def send_checkout_receipt(self, stay_id: int) -> Notification:
        """
        Send checkout receipt email to guest with itemized charges.

        Args:
            stay_id: Stay ID

        Returns:
            Notification record

        Raises:
            ValueError: If guest has no email address
        """
        stay = self.get_or_404(Stay, stay_id)
        guest = stay.guest
        reservation = stay.reservation

        if not guest.email:
            raise ValueError(f"Guest {guest.id} has no email address")

        charges = [
            {
                "description": charge.description,
                "amount": float(charge.total_amount),
                "date": charge.created_at.isoformat()
                if hasattr(charge, "created_at")
                else None,
            }
            for charge in stay.charges
        ]

        template_data = {
            "guest_name": guest.full_name,
            "confirmation_number": reservation.confirmation_number,
            "room_number": stay.room.room_number,
            "check_in_date": stay.check_in_date,
            "check_out_date": stay.check_out_date,
            "charges": charges,
            "total_amount": float(stay.total_charges),
            "num_nights": (stay.check_out_date - stay.check_in_date).days,
        }

        html_content = template_renderer.render_checkout_receipt(**template_data)

        notification = self._create_email_notification(
            recipient_email=guest.email,
            guest_id=guest.id,
            subject=f"Checkout Receipt - {reservation.confirmation_number}",
            template_name="checkout_receipt",
            template_data=template_data,
            html_content=html_content,
            reservation_id=reservation.id,
            stay_id=stay.id,
        )

        return await self._send_notification_email(notification, html_content)

    async def send_custom_email(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        template_data: Dict[str, Any],
        guest_id: Optional[int] = None,
    ) -> Notification:
        """
        Send custom email notification (generic method).

        Args:
            to_email: Recipient email address
            subject: Email subject
            template_name: Template to render
            template_data: Data for template rendering
            guest_id: Optional associated guest ID

        Returns:
            Notification record
        """
        html_content = template_renderer.render(template_name, **template_data)

        notification = self._create_email_notification(
            recipient_email=to_email,
            guest_id=guest_id,
            subject=subject,
            template_name=template_name,
            template_data=template_data,
            html_content=html_content,
        )

        return await self._send_notification_email(notification, html_content)

    def get_notification_history(
        self,
        guest_id: Optional[int] = None,
        reservation_id: Optional[int] = None,
        stay_id: Optional[int] = None,
        status: Optional[NotificationStatus] = None,
        notification_type: Optional[NotificationType] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Notification]:
        """
        Get paginated notification history with optional filters.

        Args:
            guest_id: Filter by guest ID
            reservation_id: Filter by reservation ID
            stay_id: Filter by stay ID
            status: Filter by notification status
            notification_type: Filter by type (email, sms, etc.)
            limit: Maximum results per page (default: 50, max: 100)
            offset: Pagination offset

        Returns:
            List of Notification records
        """
        limit = min(limit, 100)  # Prevent excessive queries

        query = self.db.query(Notification)

        if guest_id:
            query = query.filter(Notification.guest_id == guest_id)

        if reservation_id:
            query = query.filter(Notification.reservation_id == reservation_id)

        if stay_id:
            query = query.filter(Notification.stay_id == stay_id)

        if status:
            query = query.filter(Notification.status == status)

        if notification_type:
            query = query.filter(Notification.type == notification_type)

        notifications = (
            query.order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return notifications

    def get_failed_notifications(
        self, max_retries: int = 3, limit: int = 100
    ) -> List[Notification]:
        """
        Get failed notifications eligible for retry.

        Args:
            max_retries: Maximum retry attempts allowed
            limit: Maximum results

        Returns:
            List of failed notifications ready for retry
        """
        return (
            self.db.query(Notification)
            .filter(Notification.status == NotificationStatus.FAILED)
            .filter(Notification.retry_count < max_retries)
            .order_by(Notification.created_at.asc())
            .limit(limit)
            .all()
        )

    async def retry_notification(self, notification_id: int) -> Notification:
        """
        Retry a failed notification.

        Args:
            notification_id: ID of failed notification to retry

        Returns:
            Updated notification record

        Raises:
            ValueError: If notification not found or not in failed status
        """
        notification = self.db.query(Notification).get(notification_id)

        if not notification:
            raise ValueError(f"Notification {notification_id} not found")

        if notification.status != NotificationStatus.FAILED:
            raise ValueError(f"Notification {notification_id} is not in failed status")

        if notification.type != NotificationType.EMAIL:
            raise ValueError(f"Retry not supported for type: {notification.type}")

        # Re-render or use stored message
        html_content = notification.message or template_renderer.render(
            notification.template_name, **json.loads(notification.template_data or "{}")
        )

        return await self._send_notification_email(notification, html_content)
