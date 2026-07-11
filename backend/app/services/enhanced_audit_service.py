from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from app.services.base_service import BaseService
from app.models import AuditLog, ComplianceLog, DataAccessLog, DataRetentionPolicy


class EnhancedAuditService(BaseService):
    """
    Service for enhanced audit logging
    """

    # =========================
    # LOG DATA ACCESS
    # =========================
    def log_data_access(
        self,
        user_id: int,
        username: str,
        resource_type: str,
        resource_id: int,
        action: str,
        purpose: Optional[str] = None,
        justification: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> DataAccessLog:
        log = DataAccessLog(
            user_id=user_id,
            username=username,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            purpose=purpose,
            justification=justification,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)

        return log

    # =========================
    # LOG COMPLIANCE EVENT
    # =========================
    def log_compliance_event(
        self,
        compliance_type: str,
        action: str,
        description: str,
        status: str = "compliant",
        severity: str = "low",
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        data_subject: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> ComplianceLog:
        log = ComplianceLog(
            compliance_type=compliance_type,
            action=action,
            description=description,
            status=status,
            severity=severity,
            user_id=user_id,
            username=username,
            data_subject=data_subject,
            ip_address=ip_address,
        )

        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)

        return log

    # =========================
    # SEARCH AUDIT LOGS
    # =========================
    def search_audit_logs(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        status: Optional[str] = None,
        resource_type: Optional[str] = None,
        ip_address: Optional[str] = None,
        search_term: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Dict:
        query = self.db.query(AuditLog)

        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)

        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if action:
            query = query.filter(AuditLog.action == action)
        if status:
            query = query.filter(AuditLog.status == status)
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        if ip_address:
            query = query.filter(AuditLog.ip_address == ip_address)

        if search_term:
            pattern = f"%{search_term}%"
            query = query.filter(
                or_(
                    AuditLog.username.ilike(pattern),
                    getattr(AuditLog, "details", "").ilike(pattern),  # safe fallback
                )
            )

        total = query.count()

        logs = (
            query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
        )

        return {"logs": logs, "total": total, "skip": skip, "limit": limit}

    # =========================
    # EXPORT AUDIT LOGS
    # =========================
    def export_audit_logs(
        self,
        format: str = "csv",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[int] = None,
    ) -> str:
        logs = self.search_audit_logs(
            start_date=start_date, end_date=end_date, user_id=user_id, limit=10000
        )["logs"]

        if format == "csv":
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            writer.writerow(
                [
                    "ID",
                    "Timestamp",
                    "User ID",
                    "Username",
                    "Action",
                    "Status",
                    "IP Address",
                ]
            )

            for log in logs:
                writer.writerow(
                    [
                        log.id,
                        log.created_at.isoformat(),
                        log.user_id,
                        log.username,
                        log.action,
                        log.status,
                        log.ip_address,
                    ]
                )

            return output.getvalue()

        elif format == "json":
            import json

            return json.dumps(
                [
                    {
                        "id": log.id,
                        "timestamp": log.created_at.isoformat(),
                        "user_id": log.user_id,
                        "username": log.username,
                        "action": log.action,
                        "status": log.status,
                        "ip": log.ip_address,
                    }
                    for log in logs
                ],
                indent=2,
            )

        else:
            raise ValueError("Unsupported format")

    # =========================
    # COMPLIANCE REPORT (OPTIMIZED)
    # =========================
    def get_compliance_report(self, start_date: datetime, end_date: datetime) -> Dict:
        base_query = self.db.query(ComplianceLog).filter(
            ComplianceLog.created_at >= start_date, ComplianceLog.created_at <= end_date
        )

        total = base_query.count()

        violations = base_query.filter(ComplianceLog.status == "violation").count()

        unresolved = base_query.filter(
            ComplianceLog.resolved == False,
            ComplianceLog.status.in_(["violation", "pending"]),
        ).count()

        by_status = dict(
            self.db.query(ComplianceLog.status, func.count())
            .filter(ComplianceLog.created_at.between(start_date, end_date))
            .group_by(ComplianceLog.status)
            .all()
        )

        return {
            "total_events": total,
            "violations": violations,
            "unresolved": unresolved,
            "by_status": by_status,
            "compliance_rate": (((total - violations) / total * 100) if total else 100),
        }

    # =========================
    # SECURITY SUMMARY
    # =========================
    def get_security_summary(self, days: int = 7) -> Dict:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        def count(action: str):
            return (
                self.db.query(AuditLog)
                .filter(AuditLog.action == action, AuditLog.created_at >= cutoff)
                .count()
            )

        failed = count("failed_login")
        success = count("login")

        suspicious_ips = (
            self.db.query(AuditLog.ip_address, func.count())
            .filter(AuditLog.action == "failed_login", AuditLog.created_at >= cutoff)
            .group_by(AuditLog.ip_address)
            .having(func.count() >= 5)
            .all()
        )

        return {
            "authentication": {
                "failed": failed,
                "success": success,
                "failure_rate": (
                    (failed / (failed + success) * 100) if (failed + success) else 0
                ),
            },
            "threats": {
                "suspicious_ips": [
                    {"ip": ip, "attempts": count} for ip, count in suspicious_ips
                ]
            },
        }

    # =========================
    # DATA RETENTION
    # =========================
    def check_data_retention(self) -> Dict:
        policies = (
            self.db.query(DataRetentionPolicy)
            .filter(DataRetentionPolicy.is_active.is_(True))
            .all()
        )

        return {
            "total_policies": len(policies),
            "policies": [
                {
                    "data_type": p.data_type,
                    "retention_days": p.retention_days,
                    "status": "compliant",
                }
                for p in policies
            ],
        }
