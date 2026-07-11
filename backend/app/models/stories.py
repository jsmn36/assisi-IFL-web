"""
Stories and Highlights Models
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class Story(Base):
    """Story Model - Temporary posts that disappear after 24 hours"""

    __tablename__ = "stories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    media_url = Column(String(500), nullable=False)
    type = Column(String(50), default="image", nullable=False)  # image, video
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User")

    def __repr__(self):
        return f"<Story User: {self.user_id}, Type: {self.type}>"


class Highlight(Base):
    """Highlight Model - Curated collection of stories saved to profile"""

    __tablename__ = "highlights"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    cover_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User")
    highlight_stories = relationship("HighlightStory", back_populates="highlight", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Highlight {self.name} for User: {self.user_id}>"


class HighlightStory(Base):
    """HighlightStory Model - Junction table linking highlights and stories"""

    __tablename__ = "highlight_stories"

    id = Column(Integer, primary_key=True, index=True)
    highlight_id = Column(Integer, ForeignKey("highlights.id", ondelete="CASCADE"), nullable=False)
    story_id = Column(Integer, ForeignKey("stories.id", ondelete="CASCADE"), nullable=False)

    highlight = relationship("Highlight", back_populates="highlight_stories")
    story = relationship("Story")

    def __repr__(self):
        return f"<HighlightStory Highlight: {self.highlight_id}, Story: {self.story_id}>"
