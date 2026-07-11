"""Lightweight helper to write a single AuditLog row from any endpoint."""
from sqlalchemy.orm import Session

from app.core.tenant_context import get_tenant
from app.models import AuditLog
from app.models.tenant import DEFAULT_TENANT_ID


def write_audit(
    db: Session,
    action: str,
    resource_type: str,
    *,
    current_user=None,
    resource_id: int | None = None,
    details: str | None = None,
    status: str = "success",
    ip_address: str | None = None,
    tenant_id: int | None = None,
) -> None:
    user_id = getattr(current_user, "id", None)
    username = getattr(current_user, "username", None)

    # Resolve tenant: explicit arg > context > default tenant. The default
    # keeps pre-auth activity (e.g. failed logins) routable to the baseline
    # tenant rather than dropping the audit row.
    effective_tenant = tenant_id or get_tenant() or DEFAULT_TENANT_ID

    entry = AuditLog(
        tenant_id=effective_tenant,
        user_id=user_id,
        username=username,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        status=status,
        ip_address=ip_address,
    )
    db.add(entry)
    db.commit()
