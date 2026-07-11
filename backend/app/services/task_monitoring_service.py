"""
Task Monitoring Service
Track and monitor background tasks
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.task_history import TaskHistory
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
import json


class TaskMonitoringService:
    """
    Service for monitoring background tasks.
    Features: task history tracking, performance metrics, failure analysis.
    """

    def __init__(self, db: Session):
        self.db = db

    def record_task_start(
        self,
        task_id: str,
        task_name: str,
        task_args: list = None,
        task_kwargs: dict = None,
        queue_name: str = "default",
        worker_name: str = None,
    ) -> TaskHistory:
        """Record task start"""
        task_history = TaskHistory(
            task_id=task_id,
            task_name=task_name,
            task_args=json.dumps(task_args or []),
            task_kwargs=json.dumps(task_kwargs or {}),
            status="running",
            started_at=datetime.now(timezone.utc),
            queue_name=queue_name,
            worker_name=worker_name,
        )
        self.db.add(task_history)
        self.db.commit()
        return task_history

    def record_task_success(self, task_id: str, result):
        """Record task success"""
        task = self.db.query(TaskHistory).filter(TaskHistory.task_id == task_id).first()
        if task:
            task.status = "success"
            task.result = json.dumps(result) if result is not None else None
            task.completed_at = datetime.now(timezone.utc)
            if task.started_at:
                task.duration_seconds = int(
                    (task.completed_at - task.started_at).total_seconds()
                )
            self.db.commit()

    def record_task_failure(self, task_id: str, error: str):
        """Record task failure"""
        task = self.db.query(TaskHistory).filter(TaskHistory.task_id == task_id).first()
        if task:
            task.status = "failure"
            task.error = str(error)
            task.completed_at = datetime.now(timezone.utc)
            if task.started_at:
                task.duration_seconds = int(
                    (task.completed_at - task.started_at).total_seconds()
                )
            task.retries += 1
            self.db.commit()

    def get_task_history(self, task_id: str) -> Optional[TaskHistory]:
        """Get task history by ID"""
        return self.db.query(TaskHistory).filter(TaskHistory.task_id == task_id).first()

    def get_recent_tasks(
        self, limit: int = 50, status: str = None
    ) -> List[TaskHistory]:
        """Get recent tasks, optionally filtered by status"""
        query = self.db.query(TaskHistory)
        if status:
            query = query.filter(TaskHistory.status == status)
        return query.order_by(TaskHistory.created_at.desc()).limit(limit).all()

    def get_task_statistics(self, hours: int = 24) -> Dict:
        """Get task statistics for last N hours"""
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        total = (
            self.db.query(func.count(TaskHistory.id))
            .filter(TaskHistory.created_at >= since)
            .scalar()
            or 0
        )

        by_status = (
            self.db.query(TaskHistory.status, func.count(TaskHistory.id).label("count"))
            .filter(TaskHistory.created_at >= since)
            .group_by(TaskHistory.status)
            .all()
        )

        avg_duration = (
            self.db.query(func.avg(TaskHistory.duration_seconds))
            .filter(TaskHistory.created_at >= since, TaskHistory.status == "success")
            .scalar()
            or 0
        )

        by_name = (
            self.db.query(
                TaskHistory.task_name, func.count(TaskHistory.id).label("count")
            )
            .filter(TaskHistory.created_at >= since)
            .group_by(TaskHistory.task_name)
            .all()
        )

        return {
            "period_hours": hours,
            "total_tasks": total,
            "by_status": {s: c for s, c in by_status},
            "average_duration_seconds": round(float(avg_duration), 2),
            "by_task_name": {n: c for n, c in by_name},
        }

    def get_failed_tasks(self, limit: int = 20) -> List[TaskHistory]:
        """Get recent failed tasks"""
        return (
            self.db.query(TaskHistory)
            .filter(TaskHistory.status == "failure")
            .order_by(TaskHistory.created_at.desc())
            .limit(limit)
            .all()
        )
