"""
Task History Model
Track background task execution
"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base


class TaskHistory(Base):
    """
    Task execution history
    Tracks all background tasks for auditing and monitoring
    """

    __tablename__ = "task_history"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(255), unique=True, index=True, nullable=False)
    task_name = Column(String(255), nullable=False, index=True)
    task_args = Column(Text)
    task_kwargs = Column(Text)

    status = Column(
        String(50), nullable=False, index=True
    )  # pending, running, success, failure
    result = Column(Text)
    error = Column(Text)

    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)

    worker_name = Column(String(255))
    queue_name = Column(String(100))

    retries = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<TaskHistory {self.task_name} ({self.status})>"
