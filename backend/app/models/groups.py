"""
Groups, Classrooms, Assignments, and Events Models
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class Group(Base):
    """Group Model - Represents a community group or educational classroom"""

    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    is_classroom = Column(Boolean, default=False, nullable=False)
    class_or_department = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    creator = relationship("User")
    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="group", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="group", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Group {self.name} (Classroom: {self.is_classroom})>"


class GroupMember(Base):
    """GroupMember Model - Tracks memberships inside groups/classrooms"""

    __tablename__ = "group_members"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), default="member", nullable=False)  # member, admin
    joined_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    group = relationship("Group", back_populates="members")
    user = relationship("User")

    def __repr__(self):
        return f"<GroupMember Group: {self.group_id}, User: {self.user_id}, Role: {self.role}>"


class Event(Base):
    """Event Model - Academic or recreational event created by students or faculty"""

    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    date = Column(DateTime, nullable=False)
    location = Column(String(200), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    creator = relationship("User")
    group = relationship("Group", back_populates="events")

    def __repr__(self):
        return f"<Event {self.title} on {self.date}>"


class Assignment(Base):
    """Assignment Model - Study material or task shared within a classroom"""

    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    file_url = Column(String(500), nullable=True)
    due_date = Column(DateTime, nullable=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    creator = relationship("User")
    group = relationship("Group", back_populates="assignments")

    def __repr__(self):
        return f"<Assignment {self.title}>"
