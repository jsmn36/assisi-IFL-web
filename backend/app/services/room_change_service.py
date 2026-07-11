from typing import Optional, List, Dict
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.base_service import BaseService, BusinessRuleError
from app.models import (
    Stay,
    StayStatus,
    Room,
    OccupancyState,
    ConditionState,
    Charge,
    ChargeType,
    ChargeStatus,
)
from app.gates import RoomAssignmentGate


class RoomChangeService(BaseService):
    """
    Service for room changes

    Methods:
    - change_room: Change guest to different room
    - validate_room_change: Validate room change is possible
    - get_room_change_history: Get room change history
    """

    DEFAULT_ROOM_CHANGE_FEE = Decimal("50.00")

    def __init__(self, db: Session):
        super().__init__(db)

    # ---------------------------------------------------------
    # CHANGE ROOM
    # ---------------------------------------------------------

    def change_room(
        self,
        stay_id: int,
        new_room_id: int,
        reason: str,
        changed_by: str,
        charge_fee: bool = False,
    ) -> Stay:
        """
        Change guest to a different room.
        """

        stay: Stay = self.get_or_404(Stay, stay_id)
        old_room: Room = stay.room
        new_room: Room = self.get_or_404(Room, new_room_id)

        # Validate stay status
        if stay.status != StayStatus.CHECKED_IN:
            raise BusinessRuleError(
                f"Cannot change room for stay in status: {stay.status.value}"
            )

        # Validate different room
        if old_room.id == new_room.id:
            raise BusinessRuleError("New room must be different from current room")

        # Validate availability using gate
        gate = RoomAssignmentGate()
        result = gate.execute(
            {"room": new_room, "reservation": stay.reservation, "db": self.db}
        )

        if result.failed:
            raise BusinessRuleError(result.message, result.details)

        # Update room states
        old_room.occupancy_state = OccupancyState.VACANT
        old_room.condition_state = ConditionState.DIRTY

        new_room.occupancy_state = OccupancyState.OCCUPIED
        new_room.condition_state = ConditionState.CLEAN

        # Update stay
        old_room_number = old_room.room_number
        stay.room_id = new_room.id

        # Add note
        change_note = (
            f"Room changed from {old_room_number} "
            f"to {new_room.room_number} - Reason: {reason}"
        )

        stay.notes = f"{stay.notes}\n{change_note}" if stay.notes else change_note

        # Optional fee
        if charge_fee:
            fee = self.DEFAULT_ROOM_CHANGE_FEE

            charge = Charge(
                property_id=stay.property_id,
                reservation_id=stay.reservation_id,
                stay_id=stay.id,
                guest_id=stay.guest_id,
                charge_type=ChargeType.OTHER,
                description=f"Room change fee ({old_room_number} → {new_room.room_number})",
                amount=fee,
                total_amount=fee,
                status=ChargeStatus.POSTED,
                created_by=changed_by,
            )

            self.db.add(charge)
            self.db.flush()  # Ensure charge is persisted before totals update

            stay.add_other_charge(fee)

        self.commit()
        self.refresh(stay)

        self._log_action("change_room", "stay", stay.id, changed_by)

        return stay

    # ---------------------------------------------------------
    # VALIDATE ROOM CHANGE
    # ---------------------------------------------------------

    def validate_room_change(self, stay_id: int, new_room_id: int) -> Dict:
        """
        Validate if room change is possible.
        """

        stay: Stay = self.get_or_404(Stay, stay_id)
        new_room: Room = self.get_or_404(Room, new_room_id)

        issues: List[str] = []
        warnings: List[str] = []

        if stay.status != StayStatus.CHECKED_IN:
            issues.append(f"Stay must be checked in (current: {stay.status.value})")

        if stay.room_id == new_room_id:
            issues.append("New room must be different from current room")

        if new_room.occupancy_state != OccupancyState.VACANT:
            issues.append(
                f"Room {new_room.room_number} is " f"{new_room.occupancy_state.value}"
            )

        if new_room.condition_state != ConditionState.CLEAN:
            warnings.append(
                f"Room {new_room.room_number} is " f"{new_room.condition_state.value}"
            )

        if stay.reservation.room_type_id != new_room.room_type_id:
            warnings.append(
                f"Room type mismatch: reserved "
                f"{stay.reservation.room_type.name}, "
                f"moving to {new_room.room_type.name}"
            )

        return {
            "can_change": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "current_room": {
                "id": stay.room.id,
                "number": stay.room.room_number,
                "type": stay.room.room_type.name,
            },
            "new_room": {
                "id": new_room.id,
                "number": new_room.room_number,
                "type": new_room.room_type.name,
                "status": new_room.occupancy_state.value,
                "condition": new_room.condition_state.value,
            },
        }

    # ---------------------------------------------------------
    # ROOM CHANGE HISTORY
    # ---------------------------------------------------------

    def get_room_change_history(self, property_id: int, limit: int = 50) -> List[Dict]:
        """
        Get room change history.
        """

        stays = (
            self.db.query(Stay)
            .filter(
                Stay.property_id == property_id,
                Stay.notes.isnot(None),
                Stay.notes.ilike("%Room changed from%"),
            )
            .order_by(Stay.updated_at.desc())
            .limit(limit)
            .all()
        )

        changes: List[Dict] = []

        for stay in stays:
            for line in stay.notes.split("\n"):
                if "Room changed from" in line:
                    changes.append(
                        {
                            "stay_id": stay.id,
                            "guest_name": stay.guest.full_name,
                            "confirmation": stay.reservation.confirmation_number,
                            "change_note": line,
                            "changed_at": (
                                stay.updated_at.isoformat() if stay.updated_at else None
                            ),
                        }
                    )

        return changes
