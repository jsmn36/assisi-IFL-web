"""
Notification Preference Service
Manage user notification settings
"""
from sqlalchemy.orm import Session
from app.models.notification_preference import NotificationPreference
from typing import Dict, Optional

VALID_PREFERENCE_FIELDS = [
    "reservation_confirmation",
    "reservation_reminder",
    "reservation_cancellation",
    "payment_received",
    "payment_failed",
    "payment_reminder",
    "account_updates",
    "security_alerts",
    "system_announcements",
    "promotional_emails",
    "newsletter",
    "daily_reports",
    "weekly_reports",
    "monthly_reports",
    "email_enabled",
    "sms_enabled",
]


class NotificationPreferenceService:
    """Service for managing notification preferences"""

    def __init__(self, db: Session):
        self.db = db

    def get_or_create_preferences(self, user_id: int) -> NotificationPreference:
        """Get user preferences or create with defaults"""
        preferences = (
            self.db.query(NotificationPreference)
            .filter(NotificationPreference.user_id == user_id)
            .first()
        )

        if not preferences:
            preferences = NotificationPreference(user_id=user_id)
            self.db.add(preferences)
            self.db.commit()
            self.db.refresh(preferences)

        return preferences

    def update_preferences(self, user_id: int, updates: Dict) -> NotificationPreference:
        """Update user preferences — only valid fields are applied"""
        preferences = self.get_or_create_preferences(user_id)

        for field, value in updates.items():
            if field in VALID_PREFERENCE_FIELDS and hasattr(preferences, field):
                setattr(preferences, field, value)

        self.db.commit()
        self.db.refresh(preferences)
        return preferences

    def should_send_notification(self, user_id: int, notification_type: str) -> bool:
        """Return True if the notification type is enabled for this user"""
        preferences = self.get_or_create_preferences(user_id)

        if not preferences.email_enabled:
            return False

        if hasattr(preferences, notification_type):
            return getattr(preferences, notification_type)

        return True  # Default allow for unknown types

    def get_preferences_dict(self, user_id: int) -> Dict:
        """Return preferences as a structured dictionary"""
        p = self.get_or_create_preferences(user_id)

        return {
            "user_id": p.user_id,
            "reservation": {
                "confirmation": p.reservation_confirmation,
                "reminder": p.reservation_reminder,
                "cancellation": p.reservation_cancellation,
            },
            "payment": {
                "received": p.payment_received,
                "failed": p.payment_failed,
                "reminder": p.payment_reminder,
            },
            "system": {
                "account_updates": p.account_updates,
                "security_alerts": p.security_alerts,
                "system_announcements": p.system_announcements,
            },
            "marketing": {
                "promotional": p.promotional_emails,
                "newsletter": p.newsletter,
            },
            "reports": {
                "daily": p.daily_reports,
                "weekly": p.weekly_reports,
                "monthly": p.monthly_reports,
            },
            "delivery": {
                "email": p.email_enabled,
                "sms": p.sms_enabled,
            },
        }
