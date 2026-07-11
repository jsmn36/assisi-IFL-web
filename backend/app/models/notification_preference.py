"""
Notification Preference Model
User notification settings
"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class NotificationPreference(Base):
    """
    User notification preferences
    Controls which notifications users receive
    """

    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    # Reservation notifications
    reservation_confirmation = Column(Boolean, default=True)
    reservation_reminder = Column(Boolean, default=True)
    reservation_cancellation = Column(Boolean, default=True)

    # Payment notifications
    payment_received = Column(Boolean, default=True)
    payment_failed = Column(Boolean, default=False)
    payment_reminder = Column(Boolean, default=True)

    # System notifications
    account_updates = Column(Boolean, default=True)
    security_alerts = Column(Boolean, default=True)
    system_announcements = Column(Boolean, default=False)

    # Marketing
    promotional_emails = Column(Boolean, default=False)
    newsletter = Column(Boolean, default=False)

    # Reports (for staff)
    daily_reports = Column(Boolean, default=False)
    weekly_reports = Column(Boolean, default=False)
    monthly_reports = Column(Boolean, default=False)

    # Delivery preferences
    email_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=False)

    # Relationship
    user = relationship("User", back_populates="notification_preferences")

    def __repr__(self):
        return f"<NotificationPreference user_id={self.user_id}>"
