from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, require_role
from app.services.enhanced_email_service import EnhancedEmailService
from app.services.template_service import template_service
from app.models import User
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter(prefix="/email-templates", tags=["Email Templates"])


# ----------------------------
# Request Schemas
# ----------------------------
class TemplatePreviewRequest(BaseModel):
    template_name: str
    context: Dict[str, Any]


class TestEmailRequest(BaseModel):
    template_name: str
    to_email: str
    context: Dict[str, Any]


# ----------------------------
# Routes
# ----------------------------
@router.get("/list")
async def list_templates(
    current_user: User = Depends(require_role("admin", "manager"))
):
    """List all available email templates"""
    templates = template_service.list_templates()

    categories = {
        "Reservations": [],
        "Notifications": [],
        "Marketing": [],
        "System": [],
    }

    for template in templates:
        if "reservation" in template:
            categories["Reservations"].append(template)
        elif any(x in template for x in ["password", "account", "report"]):
            categories["System"].append(template)
        elif any(x in template for x in ["promotion", "thank_you"]):
            categories["Marketing"].append(template)
        else:
            categories["Notifications"].append(template)

    return {"categories": categories, "total": len(templates)}


@router.get("/variables/{template_name}")
async def get_template_variables(
    template_name: str, current_user: User = Depends(require_role("admin", "manager"))
):
    """Get list of variables used in template"""
    try:
        variables = template_service.get_template_variables(f"{template_name}.html")

        return {"template_name": template_name, "variables": variables}

    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Template not found: {str(e)}")


@router.post("/preview")
async def preview_template(
    request: TemplatePreviewRequest,
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    """Preview email template with sample data"""
    try:
        service = EnhancedEmailService(db)

        preview = service.preview_template(request.template_name, request.context)

        return preview

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Preview error: {str(e)}")


@router.post("/test-send")
async def send_test_email(
    request: TestEmailRequest,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Send test email"""
    try:
        service = EnhancedEmailService(db)

        success = service.send_template_email(
            to_email=request.to_email,
            template_name=request.template_name,
            context=request.context,
            subject=f"[TEST] {request.template_name}",
        )

        return {
            "success": success,
            "message": "Test email sent" if success else "Failed to send test email",
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Send error: {str(e)}")


@router.get("/sample-data/{template_name}")
async def get_sample_data(
    template_name: str, current_user: User = Depends(require_role("admin", "manager"))
):
    """Get sample data for template preview"""
    from datetime import date, timedelta

    sample_data = {
        "reservation_confirmation": {
            "guest_name": "John Doe",
            "confirmation_code": "ABC123",
            "check_in_date": str(date.today() + timedelta(days=7)),
            "check_out_date": str(date.today() + timedelta(days=10)),
            "room_type": "Deluxe King",
            "number_of_guests": 2,
            "total_amount": 450.00,
            "management_url": "https://hotelpms.com/reservations/123",
        },
        "checkin_reminder": {
            "guest_name": "Jane Smith",
            "confirmation_code": "XYZ789",
            "check_in_date": str(date.today() + timedelta(days=1)),
            "room_type": "Premium Suite",
            "management_url": "https://hotelpms.com/reservations/456",
        },
        "password_reset": {
            "user_name": "Admin User",
            "reset_url": "https://hotelpms.com/reset-password/token123",
        },
        "daily_report": {
            "report_date": str(date.today()),
            "occupancy_rate": 85.5,
            "occupied_rooms": 45,
            "total_rooms": 52,
            "revenue": 12450.00,
            "adr": 276.67,
            "checkins": 12,
            "checkouts": 8,
            "new_reservations": 15,
            "dashboard_url": "https://hotelpms.com/dashboard",
        },
    }

    return sample_data.get(
        template_name, {"message": "No sample data available for this template"}
    )
