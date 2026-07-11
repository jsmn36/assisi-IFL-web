"""
CheckOutService
Orchestrates complete check-out workflow
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.base_service import BaseService, BusinessRuleError
from app.services.stay_service import StayService
from app.services.notification_service import NotificationService
from app.models import Stay, Charge, ChargeStatus, Notification
from app.gates import CheckOutGate, PaymentGate, GateExecutor
from app.state_machines import ReservationStateMachine, StayStateMachine

logger = logging.getLogger(__name__)


class CheckOutService(BaseService):
    """
    Orchestrates complete check-out workflow

    Workflow:
        1. Get stay
        2. Validate all check-out gates
        3. Process payment (if needed)
        4. Check out guest (update reservation + stay + room)
        5. Generate final bill
        6. Update guest statistics
    """

    def __init__(self, db: Session):
        super().__init__(db)
        self.stay_service = StayService(db)
        self.notification_service = NotificationService(db)

    def check_out(
        self,
        stay_id: Optional[int] = None,
        reservation_id: Optional[int] = None,
        room_id: Optional[int] = None,
        checked_out_by: str = "frontdesk",
        payment_method: Optional[str] = None,
        force_checkout: bool = False,
    ) -> Dict[str, Any]:
        """
        Complete check-out workflow via Gate Framework.

        Args:
            stay_id: Stay ID (or use reservation_id / room_id)
            reservation_id: Find stay by reservation
            room_id: Find stay by room
            checked_out_by: User performing checkout
            payment_method: Payment method for settlement
            force_checkout: Force checkout despite warnings

        Returns:
            Dictionary with stay, bill, payment info

        Raises:
            BusinessRuleError: If validation fails or stay not found
        """
        if not stay_id and not reservation_id and not room_id:
            raise BusinessRuleError("Must provide stay_id, reservation_id, or room_id")

        try:
            # Get stay
            if stay_id:
                stay = self.stay_service.get_stay(stay_id)
            elif reservation_id:
                stay = (
                    self.db.query(Stay)
                    .filter(
                        Stay.reservation_id == reservation_id,
                        Stay.status == "checked_in",
                    )
                    .first()
                )
                if not stay:
                    raise BusinessRuleError("No active stay found for reservation")
            else:  # room_id
                stay = (
                    self.db.query(Stay)
                    .filter(Stay.room_id == room_id, Stay.status == "checked_in")
                    .first()
                )
                if not stay:
                    raise BusinessRuleError("No active stay found for room")

            if not stay:
                raise BusinessRuleError("Stay not found")

            if not stay.reservation:
                raise BusinessRuleError("Stay has no associated reservation")
            if not stay.room:
                raise BusinessRuleError("Stay has no assigned room")

            self._log_action("check_out_started", "stay", stay.id, checked_out_by)

            # Get final bill (before state changes)
            bill = self.get_final_bill(stay.id)

            # Process payment if provided
            payment_info: Dict[str, Any] = {}
            if payment_method:
                unpaid_charges = [
                    c for c in stay.charges if c.status == ChargeStatus.POSTED
                ]
                for charge in unpaid_charges:
                    charge.mark_paid(payment_method, f"Checkout-{stay.id}")

                payment_info = {
                    "method": payment_method,
                    "amount": bill["total"],
                    "charges_paid": len(unpaid_charges),
                }
                self.db.commit()

            user_id = 1
            try:
                user_id = int(checked_out_by)
            except ValueError:
                pass

            from app.gates import TransactionCoordinator, Phase4CheckOutGate
            import app.gates.base

            coordinator = TransactionCoordinator()

            # Execute Gate
            gates_sequence = [(Phase4CheckOutGate(), {"stay_id": stay.id})]

            try:
                result = coordinator.run_sequence(
                    gates_sequence, self.db, user_id=user_id
                )
            except app.gates.base.GateError as e:
                # If force checkout is false, we raise error
                if not force_checkout:
                    raise BusinessRuleError(
                        "Check-out validation failed",
                        {"failures": [str(e)], "warnings": []},
                    )
                else:
                    logger.warning("Check-out validation failed but forced: %s", e)
                    # When forced, we must manually transition since gate failed and rolled back
                    stay.status = "checked_out"
                    stay.reservation.status = "checked_out"
                    stay.room.occupancy_state = "vacant"
                    stay.room.condition_state = "dirty"
                    self.db.flush()

            # Update guest statistics
            guest = stay.reservation.guest
            if guest:
                nights = stay.number_of_nights or stay.reservation.number_of_nights or 0
                guest.update_stay_statistics(nights_stayed=nights)
            else:
                logger.warning(f"Stay {stay.id} has no guest for statistics update")

            self.db.commit()

            # Refresh related objects
            self.db.refresh(stay)
            self.db.refresh(stay.reservation)
            if stay.room:
                self.db.refresh(stay.room)
            if guest:
                self.db.refresh(guest)

            self._log_action("check_out_completed", "stay", stay.id, checked_out_by)

            return {
                "success": True,
                "stay": stay,
                "bill": bill,
                "payment": payment_info,
                "warnings": [],
                "message": (
                    f"Guest {stay.reservation.guest.full_name if stay.reservation.guest else 'Unknown'} "
                    f"checked out from room {stay.room.room_number if stay.room else 'Unknown'}"
                ),
            }

        except BusinessRuleError:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise BusinessRuleError(f"System error during check-out: {e}")

    def get_final_bill(self, stay_id: int) -> Dict[str, Any]:
        """
        Generate final bill for stay.

        Args:
            stay_id: Stay ID

        Returns:
            Dictionary with bill details

        Raises:
            BusinessRuleError: If stay not found
        """
        stay = self.stay_service.get_stay(stay_id)
        if not stay:
            raise BusinessRuleError(f"Stay {stay_id} not found")

        # Validate required relationships
        if not stay.reservation:
            raise BusinessRuleError("Stay has no associated reservation")
        if not stay.room:
            raise BusinessRuleError("Stay has no assigned room")

        # Group charges by type
        charges_by_type: Dict[str, Dict[str, Any]] = {}
        for charge in stay.charges:
            charge_type = (
                charge.charge_type.value
                if hasattr(charge.charge_type, "value")
                else str(charge.charge_type)
            )
            if charge_type not in charges_by_type:
                charges_by_type[charge_type] = {
                    "items": [],
                    "subtotal": Decimal("0.00"),
                }

            charges_by_type[charge_type]["items"].append(
                {
                    "id": charge.id,
                    "description": charge.description,
                    "date": charge.charge_date.isoformat()
                    if charge.charge_date
                    else None,
                    "amount": float(charge.amount) if charge.amount else 0.0,
                    "tax": float(charge.tax_amount) if charge.tax_amount else 0.0,
                    "total": float(charge.total_amount) if charge.total_amount else 0.0,
                    "status": charge.status.value
                    if hasattr(charge.status, "value")
                    else str(charge.status),
                }
            )
            charges_by_type[charge_type]["subtotal"] += charge.total_amount or Decimal(
                "0"
            )

        # Calculate totals from actual charges
        tax = sum((c.tax_amount or Decimal("0")) for c in stay.charges)
        total = sum((c.total_amount or Decimal("0")) for c in stay.charges)
        subtotal = total - tax

        # Payment status
        paid_charges = [c for c in stay.charges if c.status == ChargeStatus.PAID]
        unpaid_charges = [c for c in stay.charges if c.status == ChargeStatus.POSTED]
        paid_amount = sum((c.total_amount or Decimal("0")) for c in paid_charges)
        unpaid_amount = sum((c.total_amount or Decimal("0")) for c in unpaid_charges)

        # Safely get dates
        check_in_date = stay.check_in_date or stay.reservation.check_in_date
        check_out_date = stay.check_out_date or stay.reservation.check_out_date

        return {
            "stay_id": stay.id,
            "reservation": {
                "confirmation": stay.reservation.confirmation_number,
                "guest": stay.reservation.guest.full_name
                if stay.reservation.guest
                else "Unknown",
                "room": stay.room.room_number if stay.room else "Unknown",
                "check_in": check_in_date.isoformat() if check_in_date else None,
                "check_out": check_out_date.isoformat() if check_out_date else None,
                "nights": stay.number_of_nights,
            },
            "charges_by_type": charges_by_type,
            "subtotal": float(subtotal),
            "tax": float(tax),
            "total": float(total),
            "paid": float(paid_amount),
            "balance": float(unpaid_amount),
            "payment_status": "paid" if unpaid_amount == 0 else "unpaid",
        }

    async def send_checkout_receipt(self, stay_id: int) -> Optional[Notification]:
        """
        Send checkout receipt email to guest.

        Args:
            stay_id: Stay ID to send receipt for

        Returns:
            Notification record if sent successfully, None otherwise
        """
        try:
            notification = await self.notification_service.send_checkout_receipt(
                stay_id
            )
            logger.info(f"Checkout receipt sent: notification_id={notification.id}")
            return notification
        except ValueError as e:
            logger.warning(f"Cannot send checkout receipt: {e}")
            return None
        except Exception as e:
            logger.error(f"Error sending checkout receipt: {e}")
            raise
