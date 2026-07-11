"""
Audit & Compliance API Endpoints
"""
from fastapi import APIRouter, Depends, Query, Response
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.api.dependencies import get_db, require_role
from app.services.enhanced_audit_service import EnhancedAuditService
from app.models import User

router = APIRouter(prefix="/audit", tags=["Audit & Compliance"])


# Request Models
class DataAccessLogRequest(BaseModel):
    resource_type: str
    resource_id: int
    action: str
    purpose: Optional[str] = None
    justification: Optional[str] = None


class ComplianceEventRequest(BaseModel):
    compliance_type: str
    action: str
    description: str
    status: str = "compliant"
    severity: str = "low"
    data_subject: Optional[str] = None


# === Audit Logs ===
@router.get("/logs", summary="Search audit logs")
async def search_audit_logs(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    ip_address: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    """Search audit logs with advanced filtering"""
    service = EnhancedAuditService(db)

    result = service.search_audit_logs(
        start_date=start_date,
        end_date=end_date,
        user_id=user_id,
        action=action,
        status=status,
        resource_type=resource_type,
        ip_address=ip_address,
        search_term=search,
        skip=skip,
        limit=limit,
    )

    return {
        "logs": [
            {
                "id": log.id,
                "timestamp": log.created_at.isoformat(),
                "user_id": log.user_id,
                "username": log.username,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "status": log.status,
                "ip_address": log.ip_address,
                "details": log.details,
            }
            for log in result["logs"]
        ],
        "total": result["total"],
        "skip": result["skip"],
        "limit": result["limit"],
    }


@router.get("/logs/export", summary="Export audit logs")
async def export_audit_logs(
    format: str = Query("csv", regex="^(csv|json)$"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    user_id: Optional[int] = Query(None),
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Export audit logs (Admin only)"""
    service = EnhancedAuditService(db)

    data = service.export_audit_logs(
        format=format, start_date=start_date, end_date=end_date, user_id=user_id
    )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"audit_logs_{timestamp}.{format}"

    if format == "csv":
        return Response(
            content=data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    else:
        return Response(
            content=data,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )


@router.post("/data-access", summary="Log data access")
async def log_data_access(
    log_data: DataAccessLogRequest,
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    """Log sensitive data access (GDPR compliance)"""
    service = EnhancedAuditService(db)

    log = service.log_data_access(
        user_id=current_user.id,
        username=current_user.username,
        resource_type=log_data.resource_type,
        resource_id=log_data.resource_id,
        action=log_data.action,
        purpose=log_data.purpose,
        justification=log_data.justification,
    )

    return {"message": "Data access logged", "log_id": log.id}


# === Compliance ===
@router.post("/compliance", summary="Log compliance event")
async def log_compliance_event(
    event_data: ComplianceEventRequest,
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    """Log compliance event"""
    service = EnhancedAuditService(db)

    log = service.log_compliance_event(
        compliance_type=event_data.compliance_type,
        action=event_data.action,
        description=event_data.description,
        status=event_data.status,
        severity=event_data.severity,
        user_id=current_user.id,
        username=current_user.username,
        data_subject=event_data.data_subject,
    )

    return {"message": "Compliance event logged", "log_id": log.id}


@router.get("/compliance/report", summary="Get compliance report")
async def get_compliance_report(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    """Get compliance report"""
    service = EnhancedAuditService(db)

    if not start_date:
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
    if not end_date:
        end_date = datetime.now(timezone.utc)

    report = service.get_compliance_report(start_date, end_date)
    return report


@router.get("/security/summary", summary="Get security summary")
async def get_security_summary(
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    """Get security summary"""
    service = EnhancedAuditService(db)
    summary = service.get_security_summary(days=days)
    return summary


@router.get("/retention/status", summary="Get data retention status")
async def get_retention_status(
    current_user: User = Depends(require_role("admin")), db: Session = Depends(get_db)
):
    """Get data retention compliance status (Admin only)"""
    service = EnhancedAuditService(db)
    status = service.check_data_retention()
    return status


@router.get("/stats", summary="Get audit statistics")
async def get_audit_stats(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    """Get audit log statistics"""
    service = EnhancedAuditService(db)

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

    result = service.search_audit_logs(start_date=cutoff_date, limit=10000)

    logs = result["logs"]

    by_action = {}
    by_status = {}
    by_day = {}

    for log in logs:
        by_action[log.action] = by_action.get(log.action, 0) + 1
        by_status[log.status] = by_status.get(log.status, 0) + 1
        day_key = log.created_at.date().isoformat()
        by_day[day_key] = by_day.get(day_key, 0) + 1

    return {
        "period_days": days,
        "total_logs": len(logs),
        "by_action": by_action,
        "by_status": by_status,
        "by_day": by_day,
    }


# === Privileged Action Heatmap ===
from app.services.privileged_action_service import PrivilegedActionService


@router.get("/privileged/summary", summary="Privileged-action summary")
async def privileged_summary(
    since_days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    return PrivilegedActionService(db).actor_summary(since_days=since_days)


@router.get("/privileged/heatmap", summary="User × hour-of-day privileged action heatmap")
async def privileged_heatmap(
    since_days: int = Query(30, ge=1, le=365),
    only_privileged: bool = Query(True),
    top_n_users: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    return PrivilegedActionService(db).heatmap(
        since_days=since_days,
        only_privileged=only_privileged,
        top_n_users=top_n_users,
    )


@router.get("/privileged/day-of-week", summary="Privileged actions by day of week")
async def privileged_by_dow(
    since_days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    return {"buckets": PrivilegedActionService(db).by_day_of_week(since_days=since_days)}


@router.get("/privileged/top-actions", summary="Top privileged actions")
async def privileged_top_actions(
    since_days: int = Query(30, ge=1, le=365),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    return {
        "actions": PrivilegedActionService(db).top_privileged_actions(
            since_days=since_days, limit=limit
        )
    }
