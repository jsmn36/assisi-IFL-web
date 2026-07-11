"""
Post Model
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class Post(Base):
    """Post Model representing social feed updates, notice board announcements, events, etc."""

    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    type = Column(String(50), nullable=False, default="news")  # image, video, pdf, notice, announcement, event, news
    media_url = Column(String(500), nullable=True)
    is_pinned = Column(Boolean, default=False, nullable=False)
    hashtags = Column(String(500), nullable=True)  # Comma-separated list of tags
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    institution = relationship("User", back_populates="posts")

    def __repr__(self):
        return f"<Post {self.title} by User {self.institution_id}>"
