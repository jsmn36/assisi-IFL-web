from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Text,
    ForeignKey,
    JSON,
    func,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class SavedSearch(Base):
    """
    Saved Search Model
    Stores user's saved searches
    """

    __tablename__ = "saved_searches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Search configuration
    entity_type = Column(String(50), nullable=False, index=True)
    search_params = Column(JSON, nullable=False, default=dict)

    # Settings
    is_default = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)

    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_used = Column(DateTime, nullable=True)
    use_count = Column(Integer, default=0)

    # Relationships
    user = relationship("User", back_populates="saved_searches")

    def __repr__(self):
        return f"<SavedSearch id={self.id} name={self.name}>"


class SearchHistory(Base):
    """
    Search History Model
    Tracks user search history
    """

    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Search details
    entity_type = Column(String(50), nullable=False, index=True)
    search_term = Column(String(500), nullable=False)
    filters = Column(JSON, nullable=True, default=dict)

    # Results
    result_count = Column(Integer, nullable=True)

    # Metadata
    created_at = Column(DateTime, server_default=func.now(), index=True)

    # Relationships
    user = relationship("User", back_populates="search_history")

    def __repr__(self):
        return f"<SearchHistory id={self.id} entity={self.entity_type}>"


class QuickFilter(Base):
    """
    Quick Filter Model
    Predefined quick filters for common searches
    """

    __tablename__ = "quick_filters"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False, index=True)
    filter_config = Column(JSON, nullable=False, default=dict)

    # Display
    icon = Column(String(50), nullable=True)
    color = Column(String(20), nullable=True)
    display_order = Column(Integer, default=0)

    # Access control
    is_active = Column(Boolean, default=True, index=True)
    required_role = Column(String(50), nullable=True)

    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String(100), nullable=True)

    def __repr__(self):
        return f"<QuickFilter id={self.id} name={self.name}>"
