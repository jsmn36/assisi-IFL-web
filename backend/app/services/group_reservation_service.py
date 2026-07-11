from datetime import date
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.services.base_service import BaseService, ValidationError, BusinessRuleError
from app.models import GroupReservation, Reservation, ReservationStatus
import secrets


class GroupReservationService(BaseService):
    """
    Service for managing group reservations.
    """

    # ===============================
    # CREATE GROUP
    # ===============================
    def create_group(
        self,
        property_id: int,
        group_name: str,
        contact_name: str,
        contact_email: str,
        arrival_date: date,
        departure_date: date,
        number_of_rooms: int,
        group_rate: Optional[Decimal] = None,
        contact_phone: Optional[str] = None,
        notes: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> GroupReservation:
        if departure_date <= arrival_date:
            raise ValidationError("Departure date must be after arrival date")

        if number_of_rooms <= 0:
            raise ValidationError("Number of rooms must be greater than 0")

        group_code = self._generate_group_code()

        group = GroupReservation(
            property_id=property_id,
            group_name=group_name,
            group_code=group_code,
            contact_name=contact_name,
            contact_email=contact_email,
            contact_phone=contact_phone,
            arrival_date=arrival_date,
            departure_date=departure_date,
            number_of_rooms=number_of_rooms,
            group_rate=group_rate,
            notes=notes,
            status="tentative",
            rooms_blocked=0,
            rooms_confirmed=0,
            created_by=created_by,
        )

        self.db.add(group)
        self.commit()
        self.refresh(group)

        self._log_action("create_group", "group_reservation", group.id, created_by)

        return group

    # ===============================
    # ADD ROOM TO GROUP
    # ===============================
    def add_room_to_group(
        self,
        group_id: int,
        guest_id: int,
        room_type_id: int,
        num_adults: int,
        num_children: int = 0,
        special_requests: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> Reservation:
        if num_adults <= 0:
            raise ValidationError("At least one adult is required")

        group = self.get_or_404(GroupReservation, group_id)

        if group.rooms_blocked >= group.number_of_rooms:
            raise BusinessRuleError(f"Group {group.group_code} is already full")

        from app.services.reservation_service import ReservationService

        res_service = ReservationService(self.db)

        reservation = res_service.create_reservation(
            property_id=group.property_id,
            guest_id=guest_id,
            room_type_id=room_type_id,
            check_in_date=group.arrival_date,
            check_out_date=group.departure_date,
            num_adults=num_adults,
            num_children=num_children,
            nightly_rate=group.group_rate,
            special_requests=special_requests,
            created_by=created_by,
        )

        # 🔥 PROPER RELATIONSHIP (IMPORTANT)
        reservation.group_reservation_id = group.id

        group.rooms_blocked += 1

        self.commit()
        self.refresh(group)

        self._log_action("add_room_to_group", "group_reservation", group.id, created_by)

        return reservation

    # ===============================
    # CONFIRM GROUP
    # ===============================
    def confirm_group(self, group_id: int, confirmed_by: str) -> GroupReservation:
        group = self.get_or_404(GroupReservation, group_id)

        if group.status == "confirmed":
            raise BusinessRuleError("Group is already confirmed")

        from app.services.reservation_service import ReservationService

        res_service = ReservationService(self.db)

        reservations = (
            self.db.query(Reservation)
            .filter(Reservation.group_reservation_id == group.id)
            .all()
        )

        for reservation in reservations:
            if reservation.status == ReservationStatus.PENDING:
                res_service.confirm_reservation(reservation.id, confirmed_by)

        # Re-fetch updated reservations
        updated_reservations = (
            self.db.query(Reservation)
            .filter(Reservation.group_reservation_id == group.id)
            .all()
        )

        group.status = "confirmed"
        group.rooms_confirmed = sum(
            1 for r in updated_reservations if r.status == ReservationStatus.CONFIRMED
        )

        self.commit()
        self.refresh(group)

        self._log_action("confirm_group", "group_reservation", group.id, confirmed_by)

        return group

    # ===============================
    # CANCEL GROUP
    # ===============================
    def cancel_group(
        self, group_id: int, cancelled_by: str, reason: Optional[str] = None
    ) -> GroupReservation:
        group = self.get_or_404(GroupReservation, group_id)

        from app.services.reservation_service import ReservationService

        res_service = ReservationService(self.db)

        reservations = (
            self.db.query(Reservation)
            .filter(Reservation.group_reservation_id == group.id)
            .all()
        )

        for reservation in reservations:
            if reservation.status not in (
                ReservationStatus.CANCELLED,
                ReservationStatus.CHECKED_OUT,
            ):
                res_service.cancel_reservation(
                    reservation.id,
                    cancelled_by,
                    reason=f"Group cancellation: {reason}"
                    if reason
                    else "Group cancellation",
                    force_cancel=True,
                )

        group.status = "cancelled"

        self.commit()
        self.refresh(group)

        self._log_action("cancel_group", "group_reservation", group.id, cancelled_by)

        return group

    # ===============================
    # GROUP REPORT
    # ===============================
    def get_group_report(
        self,
        property_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict:
        query = self.db.query(GroupReservation).filter(
            GroupReservation.property_id == property_id
        )

        if start_date:
            query = query.filter(GroupReservation.arrival_date >= start_date)

        if end_date:
            query = query.filter(GroupReservation.departure_date <= end_date)

        groups = query.all()

        total_rooms = sum(g.number_of_rooms for g in groups)
        total_revenue = sum(g.total_value or 0 for g in groups)

        by_status = {}
        for g in groups:
            by_status[g.status] = by_status.get(g.status, 0) + 1

        return {
            "total_groups": len(groups),
            "total_rooms": total_rooms,
            "total_revenue": float(total_revenue),
            "by_status": by_status,
        }

    # ===============================
    # GENERATE GROUP CODE
    # ===============================
    def _generate_group_code(self) -> str:
        while True:
            code = f"GRP-{secrets.token_hex(4).upper()}"
            existing = (
                self.db.query(GroupReservation)
                .filter(GroupReservation.group_code == code)
                .first()
            )
            if not existing:
                return code
