"""
Institution Profile Model
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class InstitutionProfile(Base):
    """Institution Profile Model"""

    __tablename__ = "institution_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    name = Column(String(200), nullable=False, index=True)
    logo_url = Column(String(500), nullable=True)
    banner_url = Column(String(500), nullable=True)
    about = Column(Text, nullable=True)
    contact_email = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)
    website_url = Column(String(500), nullable=True)
    social_links = Column(Text, nullable=True)  # JSON-serialized string of website/social links
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="profile")

    def __repr__(self):
        return f"<InstitutionProfile {self.name}>"
