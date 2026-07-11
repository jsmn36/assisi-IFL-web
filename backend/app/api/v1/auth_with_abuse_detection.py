"""
Enhanced Auth Endpoints with Abuse Detection
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.api.dependencies import get_db
from app.services.auth_service import AuthService
from app.services.abuse_detection_service import AbuseDetectionService
from app.schemas.auth import LoginRequest, TokenResponse
from app.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request, login_data: LoginRequest, db: Session = Depends(get_db)
):
    """
    Login with abuse detection.
    Tracks failed attempts and blocks IPs after threshold.
    """
    # Get client IP
    client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    if not client_ip:
        client_ip = request.headers.get("X-Real-IP", "")
    if not client_ip and request.client:
        client_ip = request.client.host

    identifier = f"{client_ip}:{login_data.email}"

    # Check if IP is blocked
    if AbuseDetectionService.is_ip_blocked(client_ip):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your IP has been temporarily blocked due to suspicious activity",
        )

    # Check if too many failed attempts
    if AbuseDetectionService.track_failed_auth(identifier, max_failures=5):
        AbuseDetectionService.block_ip(
            client_ip, duration_seconds=3600, reason="Too many failed login attempts"
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. IP blocked for 1 hour.",
        )

    try:
        auth_service = AuthService(db)
        result = auth_service.authenticate_user(login_data.email, login_data.password)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        # Success — reset failed attempts
        AbuseDetectionService.reset_failed_auth(identifier)

        return TokenResponse(
            access_token=result["access_token"],
            token_type="bearer",
            user=result["user"],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed",
        )
