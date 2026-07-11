"""
WorkflowAutomationService
Automated workflows for housekeeping and maintenance
"""
from datetime import date, datetime, timedelta
from typing import List, Dict
from sqlalchemy.orm import Session
from app.services.base_service import BaseService
from app.services.housekeeping_service import HousekeepingService
from app.services.maintenance_service import MaintenanceService
from app.models import (
    Property,
    Room,
    RoomStatus,
    Stay,
    StayStatus,
    HousekeepingTask,
    TaskType,
    TaskPriority,
    MaintenanceRequest,
)


class WorkflowAutomationService(BaseService):
    """
    Service for automated workflows

    Methods:
    - process_daily_housekeeping: Daily housekeeping automation
    - generate_maintenance_alerts: Alert for preventive maintenance
    - optimize_task_routes: Optimize cleaning routes
    - auto_escalate_overdue: Escalate overdue tasks
    """

    def __init__(self, db: Session):
        super().__init__(db)
        self.housekeeping_service = HousekeepingService(db)
        self.maintenance_service = MaintenanceService(db)

    def process_daily_housekeeping(
        self, property_id: int, target_date: date, created_by: str
    ) -> Dict:
        """
        Process daily housekeeping automation
        """
        tasks_created = {"checkout": 0, "stayover": 0, "vacant": 0, "total": 0}

        checkouts = (
            self.db.query(Stay)
            .filter(
                Stay.property_id == property_id,
                Stay.check_out_date == target_date,
                Stay.status.in_([StayStatus.CHECKED_IN, StayStatus.RESERVED]),
            )
            .all()
        )

        for checkout in checkouts:
            existing = (
                self.db.query(HousekeepingTask)
                .filter(
                    HousekeepingTask.room_id == checkout.room_id,
                    HousekeepingTask.scheduled_date == target_date,
                    HousekeepingTask.task_type == TaskType.CHECKOUT_CLEANING,
                )
                .first()
            )

            if not existing:
                self.housekeeping_service.create_task(
                    property_id=property_id,
                    room_id=checkout.room_id,
                    task_type=TaskType.CHECKOUT_CLEANING,
                    scheduled_date=target_date,
                    priority=TaskPriority.HIGH,
                    created_by=created_by,
                )
                tasks_created["checkout"] += 1

        stayovers = (
            self.db.query(Stay)
            .filter(
                Stay.property_id == property_id,
                Stay.check_in_date < target_date,
                Stay.check_out_date > target_date,
                Stay.status == StayStatus.CHECKED_IN,
            )
            .all()
        )

        for stayover in stayovers:
            existing = (
                self.db.query(HousekeepingTask)
                .filter(
                    HousekeepingTask.room_id == stayover.room_id,
                    HousekeepingTask.scheduled_date == target_date,
                    HousekeepingTask.task_type == TaskType.STAYOVER_CLEANING,
                )
                .first()
            )

            if not existing:
                self.housekeeping_service.create_task(
                    property_id=property_id,
                    room_id=stayover.room_id,
                    task_type=TaskType.STAYOVER_CLEANING,
                    scheduled_date=target_date,
                    priority=TaskPriority.NORMAL,
                    created_by=created_by,
                )
                tasks_created["stayover"] += 1

        vacant_dirty = (
            self.db.query(Room)
            .filter(
                Room.property_id == property_id,
                Room.status == RoomStatus.DIRTY,
                Room.is_active == True,
            )
            .all()
        )

        for room in vacant_dirty:
            existing = (
                self.db.query(HousekeepingTask)
                .filter(
                    HousekeepingTask.room_id == room.id,
                    HousekeepingTask.scheduled_date == target_date,
                    HousekeepingTask.task_type == TaskType.CHECKOUT_CLEANING,
                )
                .first()
            )

            if not existing:
                self.housekeeping_service.create_task(
                    property_id=property_id,
                    room_id=room.id,
                    task_type=TaskType.CHECKOUT_CLEANING,
                    scheduled_date=target_date,
                    priority=TaskPriority.NORMAL,
                    created_by=created_by,
                )
                tasks_created["vacant"] += 1

        tasks_created["total"] = (
            tasks_created["checkout"]
            + tasks_created["stayover"]
            + tasks_created["vacant"]
        )

        return tasks_created

    def generate_maintenance_alerts(self, property_id: int) -> List[Dict]:
        alerts = []
        today = date.today()

        cutoff_date = today - timedelta(days=30)
        rooms = (
            self.db.query(Room)
            .filter(
                Room.property_id == property_id,
                Room.is_active == True,
                Room.last_cleaned < cutoff_date,
            )
            .all()
        )

        for room in rooms:
            alerts.append(
                {
                    "type": "overdue_cleaning",
                    "priority": "high",
                    "room_id": room.id,
                    "room_number": room.room_number,
                    "message": f"Room {room.room_number} not cleaned in 30+ days",
                    "last_cleaned": str(room.last_cleaned)
                    if room.last_cleaned
                    else "Never",
                }
            )

        urgent_requests = (
            self.db.query(MaintenanceRequest)
            .filter(
                MaintenanceRequest.property_id == property_id,
                MaintenanceRequest.priority == TaskPriority.URGENT,
                MaintenanceRequest.status.in_(["pending", "assigned"]),
            )
            .all()
        )

        for request in urgent_requests:
            alerts.append(
                {
                    "type": "urgent_maintenance",
                    "priority": "urgent",
                    "request_id": request.id,
                    "room_id": request.room_id,
                    "message": f"Urgent: {request.title}",
                    "created_at": request.created_at.isoformat(),
                }
            )

        return alerts

    def optimize_task_routes(self, property_id: int, target_date: date) -> Dict:
        tasks = self.housekeeping_service.get_tasks_by_date(property_id, target_date)

        floors = {}
        for task in tasks:
            if task.room and task.room.room_number:
                floor = task.room.room_number[0]
                if floor not in floors:
                    floors[floor] = []
                floors[floor].append(
                    {
                        "task_id": task.id,
                        "room_number": task.room.room_number,
                        "task_type": task.task_type.value,
                        "priority": task.priority.value,
                        "status": task.status.value,
                    }
                )

        for floor in floors:
            floors[floor].sort(key=lambda x: x["room_number"])

        return {
            "date": str(target_date),
            "total_tasks": len(tasks),
            "floors": floors,
            "floor_count": len(floors),
        }

    def auto_escalate_overdue(self, property_id: int) -> Dict:
        today = date.today()
        escalated = {"maintenance": 0, "housekeeping": 0, "total": 0}

        overdue_cutoff = today - timedelta(days=3)
        overdue_maintenance = (
            self.db.query(MaintenanceRequest)
            .filter(
                MaintenanceRequest.property_id == property_id,
                MaintenanceRequest.status.in_(["pending", "assigned", "in_progress"]),
                MaintenanceRequest.created_at
                < datetime.combine(overdue_cutoff, datetime.min.time()),
                MaintenanceRequest.priority != TaskPriority.URGENT,
            )
            .all()
        )

        for request in overdue_maintenance:
            if request.priority == TaskPriority.NORMAL:
                request.priority = TaskPriority.HIGH
                escalated["maintenance"] += 1
            elif request.priority == TaskPriority.HIGH:
                request.priority = TaskPriority.URGENT
                escalated["maintenance"] += 1

        yesterday = today - timedelta(days=1)
        overdue_tasks = (
            self.db.query(HousekeepingTask)
            .filter(
                HousekeepingTask.property_id == property_id,
                HousekeepingTask.scheduled_date < yesterday,
                HousekeepingTask.status.in_(["pending", "assigned"]),
                HousekeepingTask.priority != TaskPriority.URGENT,
            )
            .all()
        )

        for task in overdue_tasks:
            if task.priority == TaskPriority.NORMAL:
                task.priority = TaskPriority.HIGH
                escalated["housekeeping"] += 1
            elif task.priority == TaskPriority.HIGH:
                task.priority = TaskPriority.URGENT
                escalated["housekeeping"] += 1

        if escalated["maintenance"] > 0 or escalated["housekeeping"] > 0:
            self.commit()

        escalated["total"] = escalated["maintenance"] + escalated["housekeeping"]

        return escalated

    def get_daily_summary(self, property_id: int, target_date: date) -> Dict:
        tasks = self.housekeeping_service.get_tasks_by_date(property_id, target_date)

        summary = {
            "date": str(target_date),
            "total_tasks": len(tasks),
            "by_status": {
                "pending": len([t for t in tasks if t.status == "pending"]),
                "assigned": len([t for t in tasks if t.status == "assigned"]),
                "in_progress": len([t for t in tasks if t.status == "in_progress"]),
                "completed": len([t for t in tasks if t.status == "completed"]),
                "inspected": len([t for t in tasks if t.status == "inspected"]),
            },
            "by_type": {
                "checkout": len(
                    [t for t in tasks if t.task_type == TaskType.CHECKOUT_CLEANING]
                ),
                "stayover": len(
                    [t for t in tasks if t.task_type == TaskType.STAYOVER_CLEANING]
                ),
                "deep_clean": len(
                    [t for t in tasks if t.task_type == TaskType.DEEP_CLEANING]
                ),
            },
            "by_priority": {
                "urgent": len([t for t in tasks if t.priority == TaskPriority.URGENT]),
                "high": len([t for t in tasks if t.priority == TaskPriority.HIGH]),
                "normal": len([t for t in tasks if t.priority == TaskPriority.NORMAL]),
                "low": len([t for t in tasks if t.priority == TaskPriority.LOW]),
            },
        }

        completed = (
            summary["by_status"]["completed"] + summary["by_status"]["inspected"]
        )
        summary["completion_rate"] = (
            (completed / len(tasks) * 100) if len(tasks) > 0 else 0
        )

        return summary
