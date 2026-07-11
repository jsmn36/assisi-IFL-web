"""
RoomService
Business logic for room operations
"""
from typing import Optional, List
from datetime import date
from sqlalchemy.orm import Session
from app.services.base_service import BaseService, ValidationError, BusinessRuleError
from app.models import Room, RoomType, Stay, StayStatus, OccupancyState, ConditionState
from app.gates import RoomAssignmentGate, AvailabilityGate, GateExecutor


class RoomService(BaseService):
    """
    Service for room operations

    Methods:
    - get_room: Get room by ID or number
    - get_available_rooms: Get available rooms
    - assign_room: Assign room to reservation
    - change_room_status: Update room occupancy/condition
    - mark_room_clean: Mark room as clean
    - mark_room_dirty: Mark room as dirty
    - take_room_out_of_order: Take room out of service
    - return_room_to_service: Return room to service
    """

    def get_room(
        self,
        room_id: Optional[int] = None,
        room_number: Optional[str] = None,
        property_id: Optional[int] = None,
    ) -> Room:
        """
        Get room by ID or room number

        Args:
            room_id: Room ID
            room_number: Room number (requires property_id)
            property_id: Property ID (for room_number lookup)

        Returns:
            Room
        """
        if room_id:
            return self.get_or_404(Room, room_id)
        elif room_number and property_id:
            room = (
                self.db.query(Room)
                .filter(
                    Room.room_number == room_number, Room.property_id == property_id
                )
                .first()
            )
            if not room:
                raise ValidationError(f"Room {room_number} not found")
            return room
        else:
            raise ValidationError("Must provide room_id or (room_number + property_id)")

    def get_available_rooms(
        self,
        property_id: int,
        room_type_id: Optional[int] = None,
        check_in_date: Optional[date] = None,
        check_out_date: Optional[date] = None,
    ) -> List[Room]:
        """
        Get available rooms

        Args:
            property_id: Property ID
            room_type_id: Filter by room type
            check_in_date: Check availability for date range
            check_out_date: Check availability for date range

        Returns:
            List of available rooms
        """
        query = self.db.query(Room).filter(
            Room.property_id == property_id, Room.is_active == True
        )

        if room_type_id:
            query = query.filter(Room.room_type_id == room_type_id)

        # Get all rooms
        all_rooms = query.all()

        # If no date range, just check current availability
        if not check_in_date or not check_out_date:
            return [r for r in all_rooms if r.is_available()]

        # Check availability for date range
        available = []
        for room in all_rooms:
            # Check for conflicting stays
            conflicts = (
                self.db.query(Stay)
                .filter(
                    Stay.room_id == room.id,
                    Stay.status.in_([StayStatus.RESERVED, StayStatus.CHECKED_IN]),
                    Stay.check_out_date > check_in_date,
                    Stay.check_in_date < check_out_date,
                )
                .count()
            )

            if conflicts == 0 and room.is_available():
                available.append(room)

        return available

    def get_all_rooms(
        self, property_id: int, skip: int = 0, limit: int = 100
    ) -> List[Room]:
        """
        Get all rooms (regardless of availability)
        """
        return (
            self.db.query(Room)
            .filter(Room.property_id == property_id, Room.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def assign_room(
        self, room_id: int, reservation_id: int, assigned_by: Optional[str] = None
    ) -> Room:
        """
        Assign room to reservation (validates with gate)

        Args:
            room_id: Room ID
            reservation_id: Reservation ID
            assigned_by: User assigning room

        Returns:
            Assigned room
        """
        from app.models import Reservation

        room = self.get_or_404(Room, room_id)
        reservation = self.get_or_404(Reservation, reservation_id)

        # Validate with gate
        gate = RoomAssignmentGate()
        context = {"room": room, "reservation": reservation, "db": self.db}
        result = gate.execute(context)

        if result.failed:
            raise BusinessRuleError(result.message, result.details)

        self._log_action("assign_room", "room", room.id, assigned_by)

        return room

    def mark_room_clean(self, room_id: int, cleaned_by: Optional[str] = None) -> Room:
        """
        Mark room as clean

        Args:
            room_id: Room ID
            cleaned_by: Housekeeper

        Returns:
            Updated room
        """
        room = self.get_or_404(Room, room_id)

        room.mark_clean()
        self.commit()
        self.refresh(room)

        self._log_action("mark_room_clean", "room", room.id, cleaned_by)

        return room

    def mark_room_dirty(self, room_id: int, marked_by: Optional[str] = None) -> Room:
        """
        Mark room as dirty (needs cleaning)

        Args:
            room_id: Room ID
            marked_by: User marking dirty

        Returns:
            Updated room
        """
        room = self.get_or_404(Room, room_id)

        room.mark_dirty()
        self.commit()
        self.refresh(room)

        self._log_action("mark_room_dirty", "room", room.id, marked_by)

        return room

    def mark_room_inspected(
        self, room_id: int, inspected_by: Optional[str] = None
    ) -> Room:
        """
        Mark room as inspected

        Args:
            room_id: Room ID
            inspected_by: Inspector

        Returns:
            Updated room
        """
        room = self.get_or_404(Room, room_id)

        room.mark_inspected()
        self.commit()
        self.refresh(room)

        self._log_action("mark_room_inspected", "room", room.id, inspected_by)

        return room

    def take_room_out_of_order(
        self, room_id: int, reason: str, taken_by: Optional[str] = None
    ) -> Room:
        """
        Take room out of order (maintenance, damage, etc.)

        Args:
            room_id: Room ID
            reason: Reason for OOO
            taken_by: User taking out of order

        Returns:
            Updated room
        """
        room = self.get_or_404(Room, room_id)

        # Check if occupied
        if room.occupancy_state == OccupancyState.OCCUPIED:
            raise BusinessRuleError(
                f"Cannot take occupied room {room.room_number} out of order",
                {"room_number": room.room_number, "occupancy": "occupied"},
            )

        room.take_out_of_order(reason)
        self.commit()
        self.refresh(room)

        self._log_action("take_room_out_of_order", "room", room.id, taken_by)

        return room

    def return_room_to_service(
        self, room_id: int, returned_by: Optional[str] = None
    ) -> Room:
        """
        Return room to service from out of order

        Args:
            room_id: Room ID
            returned_by: User returning to service

        Returns:
            Updated room
        """
        room = self.get_or_404(Room, room_id)

        if room.occupancy_state != OccupancyState.OUT_OF_ORDER:
            raise BusinessRuleError(
                f"Room {room.room_number} is not out of order",
                {
                    "room_number": room.room_number,
                    "occupancy": room.occupancy_state.value,
                },
            )

        room.return_to_service()
        self.commit()
        self.refresh(room)

        self._log_action("return_room_to_service", "room", room.id, returned_by)

        return room

    def get_housekeeping_status(self, property_id: int) -> dict:
        """
        Get housekeeping status summary

        Args:
            property_id: Property ID

        Returns:
            Dictionary with counts by status
        """
        rooms = (
            self.db.query(Room)
            .filter(Room.property_id == property_id, Room.is_active == True)
            .all()
        )

        status = {
            "total": len(rooms),
            "vacant_clean": 0,
            "vacant_dirty": 0,
            "occupied_clean": 0,
            "occupied_dirty": 0,
            "out_of_order": 0,
            "available": 0,
        }

        for room in rooms:
            if room.occupancy_state == OccupancyState.OUT_OF_ORDER:
                status["out_of_order"] += 1
            elif room.occupancy_state == OccupancyState.VACANT:
                if room.condition_state == ConditionState.CLEAN:
                    status["vacant_clean"] += 1
                else:
                    status["vacant_dirty"] += 1
            elif room.occupancy_state == OccupancyState.OCCUPIED:
                if room.condition_state == ConditionState.CLEAN:
                    status["occupied_clean"] += 1
                else:
                    status["occupied_dirty"] += 1

            if room.is_available():
                status["available"] += 1

        return status

    def create_room(
        self,
        room_number: str,
        room_type: str,
        floor: int,
        base_price: float,
        max_occupancy: int | None = None,
    ):
        from sqlalchemy import func
        from app.models import Room, RoomType

        try:
            # Find RoomType by code or name
            room_type_obj = (
                self.db.query(RoomType)
                .filter(
                    (func.lower(RoomType.code) == room_type.lower())
                    | (func.lower(RoomType.name) == room_type.lower())
                )
                .first()
            )

            if not room_type_obj:
                room_type_obj = RoomType(
                    name=room_type.capitalize(),
                    code=room_type.upper(),
                    base_price=base_price,
                    max_occupancy=max_occupancy or 2,
                )
                self.db.add(room_type_obj)
                self.db.commit()
                self.db.refresh(room_type_obj)

            room = Room(
                room_number=room_number,
                room_type_id=room_type_obj.id,  # ✅ correct
                floor=floor,
            )
            self.db.add(room)
            self.db.commit()
            self.db.refresh(room)
            return room
        except Exception:
            self.db.rollback()
            raise
