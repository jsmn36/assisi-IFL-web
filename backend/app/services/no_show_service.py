"""
NoShowService
Handles no-show reservations and policies
"""
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from app.services.base_service import BaseService, BusinessRuleError
from app.models import (
    Reservation,
    ReservationStatus,
    Property,
    Charge,
    ChargeType,
    ChargeStatus,
)
from app.state_machines import ReservationStateMachine


class NoShowService(BaseService):
    def mark_no_show(
        self,
        reservation_id: int,
        marked_by: str,
        reason: Optional[str] = None,
        waive_fee: bool = False,
    ) -> Reservation:
        reservation = self.get_or_404(Reservation, reservation_id)

        if reservation.status != ReservationStatus.CONFIRMED:
            raise BusinessRuleError(
                f"Cannot mark reservation in status {reservation.status.value} as no-show"
            )

        today = date.today()
        if reservation.check_in_date > today:
            raise BusinessRuleError("Cannot mark as no-show before check-in date")

        sm = ReservationStateMachine(reservation, self.db)
        success, error = sm.no_show(marked_by, reason)

        if not success:
            raise BusinessRuleError(error)

        if not waive_fee:
            fee = self._calculate_no_show_fee(reservation)
            if fee > 0:
                charge = Charge(
                    property_id=reservation.property_id,
                    reservation_id=reservation.id,
                    guest_id=reservation.guest_id,
                    charge_type=ChargeType.NO_SHOW_FEE,
                    description=f"No-show fee for {reservation.confirmation_number}",
                    amount=fee,
                    total_amount=fee,
                    status=ChargeStatus.POSTED,
                    created_by=marked_by,
                )
                self.db.add(charge)

        self.commit()
        self.refresh(reservation)
        self._log_action("mark_no_show", "reservation", reservation.id, marked_by)
        return reservation

    def _calculate_no_show_fee(self, reservation: Reservation) -> Decimal:
        return reservation.nightly_rate

    def check_no_shows(
        self, property_id: int, cutoff_hours: int = 24
    ) -> List[Reservation]:
        cutoff_time = datetime.now() - timedelta(hours=cutoff_hours)
        return (
            self.db.query(Reservation)
            .filter(
                Reservation.property_id == property_id,
                Reservation.status == ReservationStatus.CONFIRMED,
                Reservation.check_in_date < cutoff_time.date(),
            )
            .all()
        )

    def get_no_show_report(
        self, property_id: int, start_date: date, end_date: date
    ) -> dict:
        no_shows = (
            self.db.query(Reservation)
            .filter(
                Reservation.property_id == property_id,
                Reservation.status == ReservationStatus.NO_SHOW,
                Reservation.check_in_date >= start_date,
                Reservation.check_in_date <= end_date,
            )
            .all()
        )

        total_reservations = (
            self.db.query(Reservation)
            .filter(
                Reservation.property_id == property_id,
                Reservation.check_in_date >= start_date,
                Reservation.check_in_date <= end_date,
            )
            .count()
        )

        no_show_rate = (
            (len(no_shows) / total_reservations * 100) if total_reservations > 0 else 0
        )
        total_lost_revenue = sum(r.total_amount for r in no_shows)

        return {
            "no_show_count": len(no_shows),
            "total_reservations": total_reservations,
            "no_show_rate": round(no_show_rate, 2),
            "total_lost_revenue": float(total_lost_revenue),
            "no_shows": no_shows,
        }
