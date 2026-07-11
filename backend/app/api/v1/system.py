"""
System API
General system configuration and data management endpoints.
"""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import Optional
import csv
import io
import json

from app.api.dependencies import get_db, get_current_user
from app import models

router = APIRouter(prefix="/system", tags=["System"])

DATA_RETENTION_DAYS = 365


@router.get("/compliance/report/{property_id}")
async def get_compliance_report(
    property_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    issues = []

    # Check for rooms with no room type
    rooms_no_type = (
        db.query(models.Room)
        .filter(models.Room.property_id == property_id, models.Room.room_type_id == None)
        .count()
    )
    if rooms_no_type:
        issues.append(f"{rooms_no_type} room(s) have no room type assigned")

    # Check for guests with no email
    guests_no_email = (
        db.query(models.Guest)
        .filter(models.Guest.property_id == property_id, models.Guest.email == None)
        .count()
    )
    if guests_no_email:
        issues.append(f"{guests_no_email} guest(s) missing email address")

    # Check for reservations stuck in pending > 7 days
    stale_cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    stale_pending = (
        db.query(models.Reservation)
        .filter(
            models.Reservation.property_id == property_id,
            models.Reservation.status == models.ReservationStatus.PENDING,
            models.Reservation.created_at < stale_cutoff,
        )
        .count()
    )
    if stale_pending:
        issues.append(f"{stale_pending} reservation(s) stuck in pending for over 7 days")

    status = "compliant" if not issues else ("non-compliant" if len(issues) > 2 else "partial")

    return {
        "status": status,
        "last_audit": datetime.now(timezone.utc).isoformat(),
        "issues": issues,
    }


@router.get("/security-summary")
async def get_security_summary(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    since = datetime.now(timezone.utc) - timedelta(hours=24)

    failed_logins = (
        db.query(models.User)
        .filter(models.User.failed_login_attempts > 0)
        .count()
    )

    active_sessions = (
        db.query(models.User)
        .filter(models.User.is_active == True)
        .count()
    )

    locked_accounts = (
        db.query(models.User)
        .filter(models.User.failed_login_attempts >= 5)
        .count()
    )

    return {
        "failed_logins": failed_logins,
        "active_sessions": active_sessions,
        "security_alerts": locked_accounts,
    }


@router.get("/audit/search/{property_id}")
async def search_audit_logs(
    property_id: int,
    query: str = Query(""),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = db.query(models.AuditLog)

    if query:
        like = f"%{query}%"
        q = q.filter(
            models.AuditLog.username.ilike(like)
            | models.AuditLog.action.ilike(like)
            | models.AuditLog.resource_type.ilike(like)
        )
    if action:
        q = q.filter(models.AuditLog.action.ilike(f"%{action}%"))
    if status:
        q = q.filter(models.AuditLog.status == status)
    if start_date:
        q = q.filter(models.AuditLog.created_at >= start_date)
    if end_date:
        q = q.filter(models.AuditLog.created_at <= end_date)

    total = q.count()
    logs = q.order_by(models.AuditLog.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "logs": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "username": log.username or "system",
                "action": log.action,
                "resource": log.resource_type or "",
                "resource_id": str(log.resource_id) if log.resource_id else "",
                "details": log.details,
                "ip_address": log.ip_address or "",
                "status": log.status,
                "created_at": log.created_at.isoformat() if log.created_at else "",
            }
            for log in logs
        ],
        "total": total,
    }


@router.get("/audit/export/{property_id}")
async def export_audit_logs(
    property_id: int,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    format: str = Query("csv"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = db.query(models.AuditLog)
    if start_date:
        q = q.filter(models.AuditLog.created_at >= start_date)
    if end_date:
        q = q.filter(models.AuditLog.created_at <= end_date)

    logs = q.order_by(models.AuditLog.created_at.desc()).limit(10000).all()
    rows = [
        {
            "id": log.id,
            "username": log.username or "system",
            "action": log.action,
            "resource": log.resource_type or "",
            "resource_id": str(log.resource_id) if log.resource_id else "",
            "status": log.status,
            "ip_address": log.ip_address or "",
            "created_at": log.created_at.isoformat() if log.created_at else "",
        }
        for log in logs
    ]

    if format == "json":
        content = json.dumps(rows, indent=2)
        return Response(content=content, media_type="application/json",
                        headers={"Content-Disposition": "attachment; filename=audit_logs.json"})

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["id", "username", "action", "resource", "resource_id", "status", "ip_address", "created_at"])
    writer.writeheader()
    writer.writerows(rows)
    return Response(content=buf.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=audit_logs.csv"})


@router.get("/retention-status")
async def get_retention_status(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    cutoff = datetime.now(timezone.utc) - timedelta(days=DATA_RETENTION_DAYS)

    eligible = (
        db.query(models.Reservation)
        .filter(
            models.Reservation.status == models.ReservationStatus.CHECKED_OUT,
            models.Reservation.updated_at < cutoff,
        )
        .count()
    )

    return {
        "data_retention_days": DATA_RETENTION_DAYS,
        "eligible_for_deletion": eligible,
        "cutoff_date": cutoff.date().isoformat(),
    }
