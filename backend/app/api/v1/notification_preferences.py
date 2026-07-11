"""
Notification Preferences API
Manage user notification settings
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, get_current_user
from app.services.notification_preference_service import NotificationPreferenceService
from app.models import User
from pydantic import BaseModel
from typing import Optional

router = APIRouter(
    prefix="/notification-preferences", tags=["Notification Preferences"]
)


class NotificationPreferenceUpdate(BaseModel):
    reservation_confirmation: Optional[bool] = None
    reservation_reminder: Optional[bool] = None
    reservation_cancellation: Optional[bool] = None
    payment_received: Optional[bool] = None
    payment_failed: Optional[bool] = None
    payment_reminder: Optional[bool] = None
    account_updates: Optional[bool] = None
    security_alerts: Optional[bool] = None
    system_announcements: Optional[bool] = None
    promotional_emails: Optional[bool] = None
    newsletter: Optional[bool] = None
    daily_reports: Optional[bool] = None
    weekly_reports: Optional[bool] = None
    monthly_reports: Optional[bool] = None
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None


@router.get("")
async def get_preferences(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get current user's notification preferences"""
    service = NotificationPreferenceService(db)
    return service.get_preferences_dict(current_user.id)


@router.put("")
async def update_preferences(
    updates: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update notification preferences — only supplied fields are changed"""
    service = NotificationPreferenceService(db)
    update_dict = {k: v for k, v in updates.dict().items() if v is not None}
    service.update_preferences(current_user.id, update_dict)

    return {
        "success": True,
        "message": "Preferences updated",
        "preferences": service.get_preferences_dict(current_user.id),
    }


@router.post("/unsubscribe/{notification_type}")
async def unsubscribe(
    notification_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Disable a single notification type by name"""
    service = NotificationPreferenceService(db)
    service.update_preferences(current_user.id, {notification_type: False})

    return {"success": True, "message": f"Unsubscribed from {notification_type}"}
