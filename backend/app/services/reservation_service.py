from sqlalchemy.orm import Session
from datetime import date, datetime, timezone
from decimal import Decimal
import uuid
import logging
from typing import Optional

from app import models, schemas
from app.services.base_service import BaseService, BusinessRuleError, ValidationError
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class ReservationService(BaseService):
    """
    Service for managing hotel reservations with integrated notifications.

    Handles reservation lifecycle: creation, confirmation, modification,
    cancellation, and automated guest communications.
    """

    def __init__(self, db: Session):
        super().__init__(db)
        self.notification_service = NotificationService(db)

    def create_reservation(
        self, res_in: Optional[schemas.ReservationCreate] = None, **kwargs
    ) -> models.Reservation:
        """
        Create a new reservation with validation and price calculation.

        Args:
            res_in: ReservationCreate schema object (optional)
            **kwargs: Alternative field arguments if res_in not provided

        Returns:
            Created Reservation model instance

        Raises:
            ValidationError: If dates are invalid or room type not found
        """
        if res_in is None:
            allowed = {
                "property_id",
                "guest_id",
                "room_type_id",
                "check_in_date",
                "check_out_date",
                "num_adults",
                "num_children",
            }
            filtered = {k: v for k, v in kwargs.items() if k in allowed}
            filtered.setdefault("num_children", 0)
            res_in = schemas.ReservationCreate(**filtered)

        today = date.today()

        if res_in.check_in_date < today:
            raise ValidationError("Check-in date cannot be in the past")

        if res_in.check_in_date >= res_in.check_out_date:
            raise ValidationError("Check-out date must be after check-in date")

        delta = res_in.check_out_date - res_in.check_in_date
        nights = max(delta.days, 1)

        room_type = self.db.get(models.RoomType, res_in.room_type_id)
        if not room_type:
            raise ValidationError(f"Room type {res_in.room_type_id} not found")

        nightly_rate = room_type.base_price

        # FIX 1: Explicit Decimal cast to avoid type mismatch with ORM Decimal fields
        total_amount = nightly_rate * Decimal(nights)

        db_res = models.Reservation(
            property_id=res_in.property_id,
            guest_id=res_in.guest_id,
            room_type_id=res_in.room_type_id,
            confirmation_number=f"RES-{uuid.uuid4().hex[:8].upper()}",
            check_in_date=res_in.check_in_date,
            check_out_date=res_in.check_out_date,
            number_of_nights=nights,
            num_adults=res_in.num_adults,
            num_children=res_in.num_children,
            nightly_rate=nightly_rate,
            total_amount=total_amount,
            status="pending",
        )

        self.db.add(db_res)
        self.db.commit()
        self.db.refresh(db_res)

        logger.info(
            f"Reservation created: {db_res.confirmation_number} (ID: {db_res.id})"
        )

        # Ghost Booking Classifier — score every new reservation. Best-effort:
        # never block creation if scoring fails. The score row itself records
        # the recommended decision; downstream front-desk workflows consume it.
        try:
            from app.services.ghost_booking_service import GhostBookingService
            GhostBookingService(self.db).score_reservation(reservation_id=db_res.id)
        except Exception:  # noqa: BLE001
            logger.exception(
                "Ghost booking scoring failed for reservation %s", db_res.id
            )

        return db_res

    def confirm_reservation(
        self, res_id: int, confirmed_by: Optional[str] = None, send_email: bool = True
    ) -> models.Reservation:
        """
        Confirm a reservation and optionally send confirmation email.

        Args:
            res_id: Reservation ID to confirm
            confirmed_by: User/system confirming the reservation
            send_email: Whether to send confirmation email (default: True)

        Returns:
            Updated Reservation model

        Raises:
            BusinessRuleError: If reservation not found
        """
        reservation = self.db.get(models.Reservation, res_id)
        if not reservation:
            raise BusinessRuleError(f"Reservation {res_id} not found")

        from app.state_machines.reservation_state_machine import ReservationStateMachine

        sm = ReservationStateMachine(reservation, self.db)
        success, error = sm.confirm(confirmed_by or "system")
        if not success:
            raise BusinessRuleError(f"Confirmation failed: {error}")

        reservation.confirmed_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(reservation)

        logger.info(
            f"Reservation {reservation.confirmation_number} confirmed by {confirmed_by}"
        )

        if send_email:
            try:
                self._send_confirmation_email(reservation.id)
            except Exception as e:
                logger.error(
                    f"Failed to send confirmation email for reservation {res_id}: {e}"
                )

        return reservation

    def _send_confirmation_email(self, reservation_id: int) -> None:
        """
        Internal method to send confirmation email via notification service.

        Args:
            reservation_id: Reservation ID to send email for
        """
        try:
            notification = self.notification_service.send_reservation_confirmation(
                reservation_id
            )
            logger.info(
                f"Confirmation email sent for reservation {reservation_id}: "
                f"notification_id={notification.id if notification else 'N/A'}"
            )
        except ValueError as e:
            logger.warning(f"Cannot send confirmation email: {e}")
        except Exception as e:
            logger.error(f"Error sending confirmation email: {e}")

    def get_reservation(
        self,
        res_id: Optional[int] = None,
        reservation_id: Optional[int] = None,
        confirmation_number: Optional[str] = None,
    ) -> Optional[models.Reservation]:
        """
        Retrieve reservation by various identifiers.

        Args:
            res_id: Reservation ID (alias)
            reservation_id: Reservation ID
            confirmation_number: Unique confirmation code

        Returns:
            Reservation model or None
        """
        if confirmation_number:
            return (
                self.db.query(models.Reservation)
                .filter(models.Reservation.confirmation_number == confirmation_number)
                .first()
            )

        # FIX 3: Use explicit `is not None` to avoid falsy bug when ID is 0
        if res_id is not None:
            id_to_use = res_id
        elif reservation_id is not None:
            id_to_use = reservation_id
        else:
            return None

        return self.db.get(models.Reservation, id_to_use)

    def get_reservation_by_confirmation(
        self, confirmation_number: str
    ) -> Optional[models.Reservation]:
        """
        Get reservation by confirmation number.

        Args:
            confirmation_number: Unique reservation confirmation code

        Returns:
            Reservation model or None
        """
        return (
            self.db.query(models.Reservation)
            .filter(models.Reservation.confirmation_number == confirmation_number)
            .first()
        )

    def cancel_reservation(
        self,
        reservation_id: int,
        cancelled_by: Optional[str] = None,
        reason: Optional[str] = None,
        send_notification: bool = True,
        force: bool = False,
    ) -> models.Reservation:
        """
        Cancel a reservation using state machine with optional notification.

        Args:
            reservation_id: Reservation to cancel
            cancelled_by: User/system performing cancellation
            reason: Cancellation reason
            send_notification: Whether to send cancellation email

        Returns:
            Updated Reservation model

        Raises:
            BusinessRuleError: If reservation not found or cannot be cancelled
        """
        reservation = self.get_reservation(reservation_id=reservation_id)
        if not reservation:
            raise BusinessRuleError("Reservation not found")

        if reservation.status == models.ReservationStatus.CHECKED_IN and not force:
            raise BusinessRuleError(
                "Cannot cancel a checked-in reservation. Use force=True for emergency cancellation."
            )

        from app.state_machines import ReservationStateMachine

        sm = ReservationStateMachine(reservation, self.db)

        success, error = sm.cancel(cancelled_by, reason=reason)
        if not success:
            raise BusinessRuleError(f"Cannot cancel reservation: {error}")

        reservation.cancellation_reason = reason
        reservation.cancelled_by = cancelled_by

        self.db.commit()
        self.db.refresh(reservation)

        logger.info(
            f"Reservation {reservation.confirmation_number} cancelled by {cancelled_by}: {reason}"
        )

        if send_notification and reservation.guest and reservation.guest.email:
            try:
                self.notification_service.send_custom_email(
                    to_email=reservation.guest.email,
                    subject=f"Reservation Cancelled - {reservation.confirmation_number}",
                    template_name="reservation_cancellation",
                    template_data={
                        "guest_name": reservation.guest.full_name,
                        "confirmation_number": reservation.confirmation_number,
                        "cancellation_reason": reason,
                        "cancelled_by": cancelled_by,
                    },
                    guest_id=reservation.guest_id,
                )
            except Exception as e:
                logger.error(f"Failed to send cancellation email: {e}")

        return reservation

    def delete_reservation(self, reservation_id: int) -> None:
        reservation = self.get_reservation(reservation_id=reservation_id)
        if not reservation:
            raise BusinessRuleError("Reservation not found")
        active_statuses = {models.ReservationStatus.CHECKED_IN}
        if reservation.status in active_statuses:
            raise BusinessRuleError("Cannot delete an active checked-in reservation")
        self.db.delete(reservation)
        self.db.commit()

    def modify_reservation(self, reservation_id: int, **kwargs) -> models.Reservation:
        """
        Modify reservation details with recalculation of totals.

        Args:
            reservation_id: Reservation to modify
            **kwargs: Fields to update (check_in_date, check_out_date, etc.)

        Returns:
            Updated Reservation model

        Raises:
            BusinessRuleError: If reservation not found
            ValidationError: If updated dates are invalid
        """
        reservation = self.get_reservation(reservation_id=reservation_id)
        if not reservation:
            raise BusinessRuleError("Reservation not found")

        allowed_fields = {
            "check_in_date",
            "check_out_date",
            "num_adults",
            "num_children",
            "special_requests",
            "room_type_id",
            "nightly_rate",
        }

        modified_dates = False
        for key, value in kwargs.items():
            if key in allowed_fields and hasattr(reservation, key):
                setattr(reservation, key, value)
                if key in ("check_in_date", "check_out_date"):
                    modified_dates = True

        if modified_dates:
            ci = reservation.check_in_date
            co = reservation.check_out_date
            if ci is None or co is None:
                raise ValidationError("Check-in and check-out dates must not be empty")
            if ci >= co:
                raise ValidationError("Check-out must be after check-in")
            nights = (co - ci).days
            reservation.number_of_nights = nights
            # FIX 4: Explicit Decimal cast to avoid type mismatch
            reservation.total_amount = reservation.nightly_rate * Decimal(nights)

        self.db.commit()
        self.db.refresh(reservation)

        logger.info(f"Reservation {reservation.confirmation_number} modified")
        return reservation

    def search_reservations(
        self,
        property_id: Optional[int] = None,
        guest_id: Optional[int] = None,
        status=None,
        check_in_date=None,
        limit: int = 100,
    ):
        """Search reservations with optional filters."""
        q = self.db.query(models.Reservation)
        if property_id is not None:
            q = q.filter(models.Reservation.property_id == property_id)
        if guest_id is not None:
            q = q.filter(models.Reservation.guest_id == guest_id)
        if status is not None:
            q = q.filter(models.Reservation.status == status)
        if check_in_date is not None:
            q = q.filter(models.Reservation.check_in_date == check_in_date)
        return q.limit(limit).all()

    async def send_check_in_reminder(self, reservation_id: int) -> None:
        """
        Send check-in reminder for reservation.

        Args:
            reservation_id: Reservation ID
        """
        try:
            notification = await self.notification_service.send_check_in_reminder(
                reservation_id
            )
            logger.info(f"Check-in reminder sent: notification_id={notification.id}")
        except ValueError as e:
            logger.warning(f"Cannot send reminder: {e}")
        except Exception as e:
            logger.error(f"Error sending check-in reminder: {e}")
            raise
