"""
Student Admission and Student Profile Models
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class StudentAdmission(Base):
    """Student Admission Model - Holds pre-registered student admission records"""

    __tablename__ = "student_admissions"

    id = Column(Integer, primary_key=True, index=True)
    admission_number = Column(String(100), unique=True, nullable=False, index=True)
    student_name = Column(String(200), nullable=False)
    class_or_department = Column(String(200), nullable=True)
    is_registered = Column(Boolean, default=False, nullable=False)

    profile = relationship("StudentProfile", back_populates="admission", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<StudentAdmission {self.admission_number} - {self.student_name}>"


class StudentProfile(Base):
    """Student Profile Model - Student specific profile attributes"""

    __tablename__ = "student_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    admission_number = Column(String(100), ForeignKey("student_admissions.admission_number", ondelete="CASCADE"), unique=True, nullable=False)
    bio = Column(Text, nullable=True)
    profile_pic_url = Column(String(500), nullable=True)
    cover_photo_url = Column(String(500), nullable=True)
    class_or_department = Column(String(200), nullable=True)
    privacy_settings = Column(String(50), default="public", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="student_profile")
    admission = relationship("StudentAdmission", back_populates="profile")

    def __repr__(self):
        return f"<StudentProfile for User ID {self.user_id}>"
