"""
HousekeepingService
Manages housekeeping tasks and assignments
"""
from datetime import date, datetime, time, timedelta, timezone
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.services.base_service import BaseService, ValidationError, BusinessRuleError
from app.models import (
    HousekeepingTask,
    TaskType,
    TaskStatus,
    TaskPriority,
    HousekeepingStaff,
    InspectionChecklist,
    Property,
    Room,
    RoomStatus,
    User,
)


class HousekeepingService(BaseService):
    """
    Service for housekeeping operations
    """

    def create_task(
        self,
        property_id: int,
        room_id: int,
        task_type: TaskType,
        scheduled_date: date,
        priority: TaskPriority = TaskPriority.NORMAL,
        scheduled_time: Optional[time] = None,
        special_instructions: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> HousekeepingTask:
        """Create housekeeping task"""
        self.get_or_404(Property, property_id)
        room = self.get_or_404(Room, room_id)

        existing = (
            self.db.query(HousekeepingTask)
            .filter(
                HousekeepingTask.room_id == room_id,
                HousekeepingTask.scheduled_date == scheduled_date,
                HousekeepingTask.task_type == task_type,
                HousekeepingTask.status.in_(
                    [TaskStatus.PENDING, TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS]
                ),
            )
            .first()
        )

        if existing:
            raise BusinessRuleError(
                f"Task already exists for room {room.room_number} on {scheduled_date}"
            )

        duration_map = {
            TaskType.CHECKOUT_CLEANING: 30,
            TaskType.STAYOVER_CLEANING: 15,
            TaskType.DEEP_CLEANING: 60,
            TaskType.TURNDOWN_SERVICE: 10,
            TaskType.INSPECTION: 15,
            TaskType.LINEN_CHANGE: 20,
            TaskType.AMENITY_REFRESH: 10,
        }
        estimated_duration = duration_map.get(task_type, 30)

        task = HousekeepingTask(
            property_id=property_id,
            room_id=room_id,
            task_type=task_type,
            priority=priority,
            scheduled_date=scheduled_date,
            scheduled_time=scheduled_time,
            estimated_duration=estimated_duration,
            special_instructions=special_instructions,
            created_by=created_by,
        )

        self.db.add(task)
        self.commit()
        self.refresh(task)
        self._log_action(
            "create_housekeeping_task", "housekeeping_task", task.id, created_by
        )
        return task

    def assign_task(
        self, task_id: int, staff_user_id: int, assigned_by: str
    ) -> HousekeepingTask:
        """Assign task to staff member"""
        task = self.get_or_404(HousekeepingTask, task_id)
        self.get_or_404(User, staff_user_id)

        if task.status not in [TaskStatus.PENDING]:
            raise BusinessRuleError(f"Task is already {task.status.value}")

        task.assigned_to = staff_user_id
        task.assigned_at = datetime.now(timezone.utc)
        task.status = TaskStatus.ASSIGNED

        self.commit()
        self.refresh(task)
        self._log_action(
            "assign_housekeeping_task", "housekeeping_task", task_id, assigned_by
        )
        return task

    def start_task(self, task_id: int, started_by: str) -> HousekeepingTask:
        """Start working on task"""
        task = self.get_or_404(HousekeepingTask, task_id)

        if task.status not in [
            TaskStatus.ASSIGNED,
            TaskStatus.PENDING,
            TaskStatus.FAILED_INSPECTION,
        ]:
            raise BusinessRuleError(
                f"Cannot start task with status {task.status.value}"
            )

        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now(timezone.utc)

        if task.room:
            task.room.status = RoomStatus.CLEANING

        self.commit()
        self.refresh(task)
        self._log_action(
            "start_housekeeping_task", "housekeeping_task", task_id, started_by
        )
        return task

    def complete_task(
        self,
        task_id: int,
        notes: Optional[str] = None,
        completed_by: Optional[str] = None,
    ) -> HousekeepingTask:
        """Mark task as completed"""
        task = self.get_or_404(HousekeepingTask, task_id)

        if task.status not in [
            TaskStatus.IN_PROGRESS,
            TaskStatus.ASSIGNED,
            TaskStatus.PENDING,
            TaskStatus.FAILED_INSPECTION,
        ]:
            raise BusinessRuleError(
                f"Cannot complete task with status {task.status.value}"
            )

        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now(timezone.utc)

        if notes:
            task.notes = notes

        if task.started_at:
            started = task.started_at
            if started.tzinfo is None:
                started = started.replace(tzinfo=timezone.utc)
            duration = (task.completed_at - started).total_seconds() / 60
            task.actual_duration = int(duration)

        if task.room and task.task_type in [
            TaskType.CHECKOUT_CLEANING,
            TaskType.DEEP_CLEANING,
        ]:
            task.room.status = RoomStatus.CLEAN

        self.commit()
        self.refresh(task)
        self._log_action(
            "complete_housekeeping_task", "housekeeping_task", task_id, completed_by
        )
        return task

    def inspect_task(
        self,
        task_id: int,
        passed: bool,
        inspector_user_id: int,
        notes: Optional[str] = None,
    ) -> HousekeepingTask:
        """Inspect completed task"""
        task = self.get_or_404(HousekeepingTask, task_id)

        if task.status not in [
            TaskStatus.COMPLETED,
            TaskStatus.FAILED_INSPECTION,
            TaskStatus.IN_PROGRESS,
            TaskStatus.ASSIGNED,
            TaskStatus.PENDING,
        ]:
            raise BusinessRuleError(
                f"Cannot inspect task with status {task.status.value}"
            )

        self.get_or_404(User, inspector_user_id)

        task.inspected_by = inspector_user_id
        task.inspected_at = datetime.now(timezone.utc)
        task.inspection_passed = passed
        task.inspection_notes = notes

        if passed:
            task.status = TaskStatus.INSPECTED
            if task.room:
                task.room.status = RoomStatus.AVAILABLE
                task.room.last_cleaned = date.today()
        else:
            task.status = TaskStatus.FAILED_INSPECTION
            if task.room:
                task.room.status = RoomStatus.DIRTY

        self.commit()
        self.refresh(task)
        self._log_action(
            "inspect_housekeeping_task",
            "housekeeping_task",
            task_id,
            f"inspector_{inspector_user_id}",
        )
        return task

    def get_tasks_by_date(
        self, property_id: int, target_date: date, status: Optional[TaskStatus] = None
    ) -> List[HousekeepingTask]:
        """Get tasks for specific date"""
        query = self.db.query(HousekeepingTask).filter(
            HousekeepingTask.property_id == property_id,
            HousekeepingTask.scheduled_date == target_date,
        )
        if status:
            query = query.filter(HousekeepingTask.status == status)
        return query.order_by(
            HousekeepingTask.priority.desc(), HousekeepingTask.scheduled_time
        ).all()

    def get_pending_tasks(
        self, property_id: int, include_assigned: bool = True
    ) -> List[HousekeepingTask]:
        """Get pending tasks"""
        statuses = [TaskStatus.PENDING]
        if include_assigned:
            statuses.append(TaskStatus.ASSIGNED)

        return (
            self.db.query(HousekeepingTask)
            .filter(
                HousekeepingTask.property_id == property_id,
                HousekeepingTask.status.in_(statuses),
                HousekeepingTask.scheduled_date <= date.today(),
            )
            .order_by(HousekeepingTask.priority.desc(), HousekeepingTask.scheduled_date)
            .all()
        )

    def auto_assign_tasks(
        self, property_id: int, target_date: date, assigned_by: str
    ) -> Dict:
        """Automatically assign tasks to available staff"""
        tasks = (
            self.db.query(HousekeepingTask)
            .filter(
                HousekeepingTask.property_id == property_id,
                HousekeepingTask.scheduled_date == target_date,
                HousekeepingTask.status == TaskStatus.PENDING,
            )
            .order_by(HousekeepingTask.priority.desc())
            .all()
        )

        if not tasks:
            return {"assigned": 0, "total": 0, "message": "No pending tasks"}

        staff = (
            self.db.query(HousekeepingStaff)
            .filter(
                HousekeepingStaff.property_id == property_id,
                HousekeepingStaff.is_active == True,
                HousekeepingStaff.role == "housekeeper",
            )
            .all()
        )

        if not staff:
            raise BusinessRuleError("No available housekeeping staff")

        assigned_count = 0
        staff_index = 0

        for task in tasks:
            staff_member = staff[staff_index % len(staff)]
            self.assign_task(task.id, staff_member.user_id, assigned_by)
            assigned_count += 1
            staff_index += 1

        return {
            "assigned": assigned_count,
            "total": len(tasks),
            "staff_count": len(staff),
            "message": f"Assigned {assigned_count} tasks to {len(staff)} staff members",
        }

    def create_checkout_tasks(
        self, property_id: int, checkout_date: date, created_by: str
    ) -> List[HousekeepingTask]:
        """Create checkout cleaning tasks for departures"""
        from app.models import Stay, StayStatus

        checkouts = (
            self.db.query(Stay)
            .filter(
                Stay.property_id == property_id,
                Stay.check_out_date == checkout_date,
                Stay.status == StayStatus.CHECKED_IN,
            )
            .all()
        )

        tasks = []
        for checkout in checkouts:
            existing = (
                self.db.query(HousekeepingTask)
                .filter(
                    HousekeepingTask.room_id == checkout.room_id,
                    HousekeepingTask.scheduled_date == checkout_date,
                    HousekeepingTask.task_type == TaskType.CHECKOUT_CLEANING,
                )
                .first()
            )

            if not existing:
                task = self.create_task(
                    property_id=property_id,
                    room_id=checkout.room_id,
                    task_type=TaskType.CHECKOUT_CLEANING,
                    scheduled_date=checkout_date,
                    priority=TaskPriority.HIGH,
                    created_by=created_by,
                )
                tasks.append(task)

        return tasks

    def get_staff(self, property_id: int) -> List[HousekeepingStaff]:
        """Get all housekeeping staff for a property"""
        return (
            self.db.query(HousekeepingStaff)
            .filter(HousekeepingStaff.property_id == property_id)
            .all()
        )

    def create_staff_member(
        self, property_id: int, user_id: int, role: str = "housekeeper"
    ) -> HousekeepingStaff:
        """Register a user as housekeeping staff"""
        self.get_or_404(Property, property_id)
        self.get_or_404(User, user_id)

        existing = (
            self.db.query(HousekeepingStaff)
            .filter_by(property_id=property_id, user_id=user_id)
            .first()
        )
        if existing:
            existing.is_active = True
            self.commit()
            return existing

        staff = HousekeepingStaff(property_id=property_id, user_id=user_id, role=role)
        self.db.add(staff)
        self.commit()
        self.refresh(staff)
        return staff

    def update_staff_member(self, staff_id: int, **kwargs) -> HousekeepingStaff:
        """Update staff member details"""
        staff = self.get_or_404(HousekeepingStaff, staff_id)
        for key, value in kwargs.items():
            if hasattr(staff, key):
                setattr(staff, key, value)
        self.commit()
        self.refresh(staff)
        return staff
