"""
API Dependencies
Authentication, authorization, and rate limiting
"""
from functools import wraps
from typing import Callable, Optional

from fastapi import Depends, HTTPException, Header, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.rate_limiter import rate_limiter
from app.core.request_context import set_user_id
from app.core.security import verify_token
from app.core.tenant_context import bypass_tenant_filter, get_tenant
from app.database import SessionLocal, get_db
from app.models import User, UserTenant

security = HTTPBearer()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    db: Session = Depends(get_db),
) -> User:
    """Extract and verify JWT token, return current user from DB"""

    token = request.cookies.get("access_token")
    if not token and credentials:
        token = credentials.credentials

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # In Phase 9, 'sub' enforces stringified user.id
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid sub format",
        )

    # The User table is NOT tenant-scoped (a user can belong to multiple
    # tenants), and looking up the user before the tenant filter is set
    # must succeed regardless. Bypass the row filter here.
    with bypass_tenant_filter():
        user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found for token payload",
        )

    # Validate tenant claim ↔ membership. Superadmins skip this check; their
    # impersonation is gated separately in the tenant middleware.
    if not payload.get("is_superadmin"):
        claim_tenant = payload.get("tenant_id")
        if claim_tenant is not None:
            try:
                claim_tenant_int = int(claim_tenant)
            except (TypeError, ValueError):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid tenant_id claim",
                )
            with bypass_tenant_filter():
                membership = (
                    db.query(UserTenant)
                    .filter(
                        UserTenant.user_id == user_id,
                        UserTenant.tenant_id == claim_tenant_int,
                    )
                    .first()
                )
            if membership is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User has no membership in claimed tenant",
                )

    # Stash on the request and contextvar so log lines + audit rows pick
    # it up without each handler having to thread it through.
    set_user_id(user.id)
    request.state.user = user
    return user


def get_current_tenant_id(request: Request) -> int:
    """Resolve the current tenant id, raising 400 if absent.

    Use this in handlers that explicitly need the tenant id (e.g. for
    seeding new rows on tables that aren't TenantScopedMixin yet). The
    middleware also stashes it on ``request.state.tenant_id``.
    """
    tid = getattr(request.state, "tenant_id", None) or get_tenant()
    if tid is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context is required for this endpoint",
        )
    return tid


def get_cache_control(cache_control: Optional[str] = Header(None)) -> Optional[str]:
    return cache_control


def get_if_none_match(if_none_match: Optional[str] = Header(None)) -> Optional[str]:
    return if_none_match


def require_role(*roles: str):
    def role_checker(current_user=Depends(get_current_user)):
        if not hasattr(current_user, "role") or current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {list(roles)}",
            )
        return current_user

    return role_checker


def get_room_service(db: Session = Depends(get_db)):
    from app.services.room_service import RoomService

    return RoomService(db)


def get_guest_service(db: Session = Depends(get_db)):
    from app.services.guest_service import GuestService

    return GuestService(db)


def get_reservation_service(db: Session = Depends(get_db)):
    from app.services.reservation_service import ReservationService

    return ReservationService(db)


def get_stay_service(db: Session = Depends(get_db)):
    from app.services.stay_service import StayService

    return StayService(db)


def get_check_in_service(db: Session = Depends(get_db)):
    from app.services.check_in_service import CheckInService

    return CheckInService(db)


def get_check_out_service(db: Session = Depends(get_db)):
    from app.services.check_out_service import CheckOutService

    return CheckOutService(db)


def rate_limit(
    max_requests: int, window_seconds: int, key_func: Optional[Callable] = None
):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Optional[Request] = kwargs.get("request")

            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if request:
                if key_func:
                    key = key_func(request)
                else:
                    client_ip = request.client.host if request.client else "unknown"
                    key = f"{client_ip}:{request.url.path}"

                allowed, info = rate_limiter.check_rate_limit(
                    key=key,
                    max_requests=max_requests,
                    window_seconds=window_seconds,
                    namespace="custom_limit",
                )

                if not allowed:
                    retry_after = info.get("retry_after", window_seconds)
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail={
                            "error": "rate_limit_exceeded",
                            "message": "Too many requests",
                            "retry_after": retry_after,
                        },
                        headers={"Retry-After": str(retry_after)},
                    )

            return await func(*args, **kwargs)

        return wrapper

    return decorator
