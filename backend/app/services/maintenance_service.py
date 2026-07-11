from datetime import date, datetime, timezone
from typing import List, Optional, Dict
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.services.base_service import BaseService, ValidationError, BusinessRuleError
from app.models import (
    MaintenanceRequest,
    TaskPriority,
    Property,
    Room,
    RoomStatus,
    User,
)


class MaintenanceService(BaseService):
    """
    Service for maintenance operations
    """

    ACTIVE_STATUSES = ["pending", "assigned", "in_progress"]

    def create_request(
        self,
        property_id: int,
        title: str,
        description: str,
        category: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        room_id: Optional[int] = None,
        location_details: Optional[str] = None,
        reported_by: Optional[str] = None,
        due_date: Optional[date] = None,
        created_by: Optional[str] = None,
    ) -> MaintenanceRequest:
        self.get_or_404(Property, property_id)

        if due_date and due_date < date.today():
            raise ValidationError("Due date cannot be in the past")

        room = None
        if room_id:
            room = self.get_or_404(Room, room_id)

            if room.property_id != property_id:
                raise ValidationError("Room does not belong to property")

            if priority == TaskPriority.URGENT:
                room.status = RoomStatus.OUT_OF_ORDER

        request = MaintenanceRequest(
            property_id=property_id,
            room_id=room_id,
            title=title,
            description=description,
            category=category,
            priority=priority,
            location_details=location_details,
            reported_by=reported_by,
            due_date=due_date,
            created_by=created_by,
        )

        self.db.add(request)
        self.commit()
        self.refresh(request)

        self._log_action(
            "create_maintenance_request", "maintenance_request", request.id, created_by
        )

        return request

    def assign_request(
        self,
        request_id: int,
        technician_user_id: int,
        scheduled_date: Optional[date] = None,
        assigned_by: Optional[str] = None,
    ) -> MaintenanceRequest:
        request = self.get_or_404(MaintenanceRequest, request_id)
        self.get_or_404(User, technician_user_id)

        if request.status != "pending":
            raise BusinessRuleError(
                f"Cannot assign request with status {request.status}"
            )

        request.assigned_to = technician_user_id
        request.assigned_at = datetime.now(timezone.utc)
        request.status = "assigned"
        request.scheduled_date = scheduled_date

        self.commit()
        self.refresh(request)

        self._log_action(
            "assign_maintenance_request", "maintenance_request", request_id, assigned_by
        )

        return request

    def start_work(self, request_id: int, started_by: str) -> MaintenanceRequest:
        request = self.get_or_404(MaintenanceRequest, request_id)

        if request.status not in ["pending", "assigned", "completed", "closed"]:
            raise BusinessRuleError(f"Cannot start work with status {request.status}")

        request.status = "in_progress"
        request.started_at = datetime.now(timezone.utc)

        self.commit()
        self.refresh(request)

        self._log_action(
            "start_maintenance_work", "maintenance_request", request_id, started_by
        )

        return request

    def complete_work(
        self,
        request_id: int,
        resolution_notes: str,
        actual_cost: Optional[Decimal] = None,
        completed_by: Optional[str] = None,
    ) -> MaintenanceRequest:
        request = self.get_or_404(MaintenanceRequest, request_id)

        if request.status not in ["in_progress", "assigned", "pending"]:
            raise BusinessRuleError(
                f"Cannot complete work with status {request.status}"
            )

        request.status = "completed"
        request.completed_at = datetime.now(timezone.utc)
        request.resolution_notes = resolution_notes

        if actual_cost is not None:
            request.actual_cost = int(
                (actual_cost * Decimal("100")).quantize(Decimal("1"))
            )

        if request.room and request.room.status == RoomStatus.OUT_OF_ORDER:
            request.room.status = RoomStatus.DIRTY

        self.commit()
        self.refresh(request)

        self._log_action(
            "complete_maintenance_work", "maintenance_request", request_id, completed_by
        )

        return request

    def close_request(self, request_id: int, closed_by: str) -> MaintenanceRequest:
        request = self.get_or_404(MaintenanceRequest, request_id)

        if request.status not in ["completed", "in_progress", "assigned", "pending"]:
            raise BusinessRuleError("Can only close active or completed requests")

        request.status = "closed"
        request.closed_at = datetime.now(timezone.utc)

        self.commit()
        self.refresh(request)

        self._log_action(
            "close_maintenance_request", "maintenance_request", request_id, closed_by
        )

        return request

    def get_active_requests(
        self,
        property_id: int,
        category: Optional[str] = None,
        priority: Optional[TaskPriority] = None,
    ) -> List[MaintenanceRequest]:
        query = self.db.query(MaintenanceRequest).filter(
            MaintenanceRequest.property_id == property_id,
            MaintenanceRequest.status.in_(self.ACTIVE_STATUSES),
        )

        if category:
            query = query.filter(MaintenanceRequest.category == category)

        if priority:
            query = query.filter(MaintenanceRequest.priority == priority)

        return query.order_by(
            MaintenanceRequest.priority.desc(), MaintenanceRequest.created_at
        ).all()

    def get_overdue_requests(self, property_id: int) -> List[MaintenanceRequest]:
        today = date.today()

        return (
            self.db.query(MaintenanceRequest)
            .filter(
                MaintenanceRequest.property_id == property_id,
                MaintenanceRequest.status.in_(self.ACTIVE_STATUSES),
                MaintenanceRequest.due_date < today,
            )
            .order_by(MaintenanceRequest.due_date)
            .all()
        )

    def get_request_stats(
        self, property_id: int, start_date: date, end_date: date
    ) -> Dict:
        total = (
            self.db.query(func.count(MaintenanceRequest.id))
            .filter(
                MaintenanceRequest.property_id == property_id,
                MaintenanceRequest.created_at.between(
                    datetime.combine(start_date, datetime.min.time()),
                    datetime.combine(end_date, datetime.max.time()),
                ),
            )
            .scalar()
        )

        completed = (
            self.db.query(func.count(MaintenanceRequest.id))
            .filter(
                MaintenanceRequest.property_id == property_id,
                MaintenanceRequest.status.in_(["completed", "closed"]),
            )
            .scalar()
        )

        return {
            "total": total,
            "completed": completed,
            "completion_rate": (completed / total * 100) if total else 0,
        }
