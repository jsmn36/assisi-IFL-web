from datetime import timezone

"""
Test Enhanced Audit Service
"""
import pytest
from datetime import datetime, timedelta
from app.services.enhanced_audit_service import EnhancedAuditService
from app.services.auth_service import AuthService
from app.models import User, AuditLog


def test_log_data_access(test_db):
    """Test logging data access"""
    auth_service = AuthService(test_db)
    audit_service = EnhancedAuditService(test_db)

    user = auth_service.create_user(
        username="audituser1", email="audit1@example.com", password="password123"
    )

    log = audit_service.log_data_access(
        user_id=user.id,
        username=user.username,
        resource_type="guest",
        resource_id=123,
        action="view",
        purpose="Customer service",
        ip_address="192.168.1.1",
    )

    assert log.user_id == user.id
    assert log.resource_type == "guest"
    assert log.resource_id == 123
    assert log.action == "view"
    assert log.purpose == "Customer service"


def test_log_compliance_event(test_db):
    """Test logging compliance event"""
    audit_service = EnhancedAuditService(test_db)

    log = audit_service.log_compliance_event(
        compliance_type="gdpr",
        action="data_export",
        description="User requested data export",
        status="compliant",
        severity="low",
        data_subject="user@example.com",
    )

    assert log.compliance_type == "gdpr"
    assert log.action == "data_export"
    assert log.status == "compliant"
    assert log.severity == "low"


def test_search_audit_logs(test_db):
    """Test searching audit logs"""
    auth_service = AuthService(test_db)
    audit_service = EnhancedAuditService(test_db)

    user = auth_service.create_user(
        username="audituser2", email="audit2@example.com", password="password123"
    )

    auth_service.authenticate_user("audituser2", "password123")

    result = audit_service.search_audit_logs(action="login", limit=10)

    assert result["total"] > 0
    assert len(result["logs"]) > 0


def test_search_with_date_range(test_db):
    """Test searching with date range"""
    auth_service = AuthService(test_db)
    audit_service = EnhancedAuditService(test_db)

    user = auth_service.create_user(
        username="audituser3", email="audit3@example.com", password="password123"
    )

    for i in range(3):
        auth_service.authenticate_user("audituser3", "password123")

    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=1)

    result = audit_service.search_audit_logs(
        start_date=start_date, end_date=end_date, user_id=user.id
    )

    assert result["total"] > 0


def test_export_audit_logs_csv(test_db):
    """Test exporting audit logs to CSV"""
    auth_service = AuthService(test_db)
    audit_service = EnhancedAuditService(test_db)

    user = auth_service.create_user(
        username="audituser4", email="audit4@example.com", password="password123"
    )

    auth_service.authenticate_user("audituser4", "password123")

    csv_data = audit_service.export_audit_logs(format="csv")

    assert csv_data is not None
    assert "ID,Timestamp,User ID" in csv_data
    assert "audituser4" in csv_data


def test_export_audit_logs_json(test_db):
    """Test exporting audit logs to JSON"""
    auth_service = AuthService(test_db)
    audit_service = EnhancedAuditService(test_db)

    user = auth_service.create_user(
        username="audituser5", email="audit5@example.com", password="password123"
    )

    auth_service.authenticate_user("audituser5", "password123")

    json_data = audit_service.export_audit_logs(format="json")

    assert json_data is not None
    assert "audituser5" in json_data


def test_get_compliance_report(test_db):
    """Test getting compliance report"""
    audit_service = EnhancedAuditService(test_db)

    for i in range(5):
        audit_service.log_compliance_event(
            compliance_type="gdpr",
            action="data_access",
            description=f"Access {i}",
            status="compliant" if i < 4 else "violation",
            severity="low",
        )

    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=7)

    report = audit_service.get_compliance_report(start_date, end_date)

    assert report["total_events"] == 5
    assert report["violations"] == 1
    assert report["compliance_rate"] == 80.0


def test_get_security_summary(test_db):
    """Test getting security summary"""
    auth_service = AuthService(test_db)
    audit_service = EnhancedAuditService(test_db)

    user = auth_service.create_user(
        username="audituser6", email="audit6@example.com", password="password123"
    )

    auth_service.authenticate_user("audituser6", "password123")
    auth_service.authenticate_user("audituser6", "wrongpassword")

    summary = audit_service.get_security_summary(days=7)

    assert "authentication" in summary
    assert summary["authentication"]["success"] >= 1
    assert summary["authentication"]["failed"] >= 1


def test_check_data_retention(test_db):
    """Test checking data retention"""
    audit_service = EnhancedAuditService(test_db)

    status = audit_service.check_data_retention()

    assert "policies" in status
    assert "total_policies" in status
