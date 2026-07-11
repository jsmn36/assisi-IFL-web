"""
CheckInService
Orchestrates complete check-in workflow
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.services.base_service import BaseService, BusinessRuleError
from app.services.reservation_service import ReservationService
from app.services.stay_service import StayService
from app.services.room_service import RoomService
from app.services.notification_service import NotificationService
from app.models import Reservation, Stay, Room, Notification
from app.gates import CheckInGate, RoomAssignmentGate, PaymentGate, GateExecutor
from app.state_machines import ReservationStateMachine

logger = logging.getLogger(__name__)


class CheckInService(BaseService):
    """
    Orchestrates complete check-in workflow

    Workflow:
    1. Validate reservation ready for check-in
    2. Assign room (if not already assigned)
    3. Create stay (if doesn't exist)
    4. Validate all check-in gates
    5. Check in guest (update reservation + stay + room)
    6. Post initial charges (optional)
    """

    VALID_CHECK_IN_STATUSES = {"confirmed", "pending"}

    def __init__(self, db: Session):
        super().__init__(db)
        self.reservation_service = ReservationService(db)
        self.stay_service = StayService(db)
        self.room_service = RoomService(db)
        self.notification_service = NotificationService(db)

    def check_in(
        self,
        reservation_id: Optional[int] = None,
        confirmation_number: Optional[str] = None,
        room_id: Optional[int] = None,
        room_number: Optional[str] = None,
        checked_in_by: str = "frontdesk",
        post_room_charges: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute complete check-in workflow using the Gate Framework.

        Args:
            reservation_id: Reservation ID
            confirmation_number: Alternative lookup by confirmation number
            room_id: Specific room ID to assign
            room_number: Specific room number to assign
            checked_in_by: User performing check-in
            post_room_charges: Whether to post initial room charges

        Returns:
            Dictionary with check-in result details

        Raises:
            BusinessRuleError: If validation fails or no rooms available
        """
        if not reservation_id and not confirmation_number:
            raise BusinessRuleError(
                "Either reservation_id or confirmation_number must be provided"
            )

        try:
            # Get reservation
            reservation = self.reservation_service.get_reservation(
                reservation_id=reservation_id, confirmation_number=confirmation_number
            )

            if not reservation:
                raise BusinessRuleError("Reservation not found")

            # Determine Room
            if not room_id and not room_number:
                if not reservation.room_type:
                    raise BusinessRuleError("Reservation has no room type assigned")

                available_rooms = self.room_service.get_available_rooms(
                    property_id=reservation.property_id,
                    room_type_id=reservation.room_type_id,
                    check_in_date=reservation.check_in_date,
                    check_out_date=reservation.check_out_date,
                )
                if not available_rooms:
                    raise BusinessRuleError(
                        f"No available {reservation.room_type.name} rooms",
                        {"room_type": reservation.room_type.name},
                    )
                room = available_rooms[0]
            else:
                room = self.room_service.get_room(
                    room_id=room_id,
                    room_number=room_number,
                    property_id=reservation.property_id,
                )

            if not room:
                raise BusinessRuleError("Room not found")

            self._log_action(
                "check_in_started", "reservation", reservation.id, checked_in_by
            )

            user_id = 1  # Or get from checked_in_by contextual if int
            try:
                user_id = int(checked_in_by)
            except ValueError:
                pass

            # Prepare Gate Sequence
            from app.gates import (
                TransactionCoordinator,
                Phase4RoomAssignmentGate,
                Phase4CheckInGate,
            )

            coordinator = TransactionCoordinator()

            gates_sequence = []

            # 1. Assign Room
            gates_sequence.append(
                (
                    Phase4RoomAssignmentGate(),
                    {"reservation_id": reservation.id, "room_id": room.id},
                )
            )

            # 2. Check In guest (mutates constraints and creates stay)
            gates_sequence.append(
                (Phase4CheckInGate(), {"reservation_id": reservation.id})
            )

            import app.gates.base

            try:
                result = coordinator.run_sequence(
                    gates_sequence, self.db, user_id=user_id
                )
            except app.gates.base.GateError as e:
                raise BusinessRuleError(f"Check-in validation failed: {e}")

            stay_id = result.get("stay_id")
            if not stay_id:
                raise BusinessRuleError("Stay was not created during check-in")

            from app.models.stay import Stay

            stay = self.db.query(Stay).filter(Stay.id == stay_id).first()

            # Post charges if requested
            charges: List[Any] = []
            if post_room_charges:
                charges = self.stay_service.post_room_charges(
                    stay_id=stay.id, posted_by=checked_in_by
                )
                self.db.commit()

            self.db.refresh(reservation)
            self.db.refresh(stay)
            self.db.refresh(room)

            self._log_action(
                "check_in_completed", "reservation", reservation.id, checked_in_by
            )

            return {
                "success": True,
                "reservation": reservation,
                "stay": stay,
                "room": room,
                "charges_posted": len(charges),
                "warnings": [],
                "message": f"Guest {reservation.guest.full_name} checked in to room {room.room_number}",
            }

        except BusinessRuleError:
            raise
        except Exception as e:
            self.db.rollback()
            raise BusinessRuleError(f"System error during check-in: {e}")

    async def send_check_in_reminder(
        self, reservation_id: int
    ) -> Optional[Notification]:
        """
        Send check-in reminder email to guest.

        Args:
            reservation_id: Reservation ID to send reminder for

        Returns:
            Notification record if sent successfully, None otherwise
        """
        try:
            notification = await self.notification_service.send_check_in_reminder(
                reservation_id
            )
            logger.info(f"Check-in reminder sent: notification_id={notification.id}")
            return notification
        except ValueError as e:
            logger.warning(f"Cannot send reminder: {e}")
            return None
        except Exception as e:
            logger.error(f"Error sending check-in reminder: {e}")
            raise
