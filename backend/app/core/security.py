"""
Security Utilities
Password hashing, JWT tokens, etc.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
from passlib.context import CryptContext
from jose import JWTError, jwt
import secrets

import os
import sys

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

from app.config import settings

# JWT settings
SECRET_KEY = settings.JWT_SECRET_KEY

if not SECRET_KEY:
    if "pytest" in sys.modules:
        SECRET_KEY = "dummy-test-key-for-pytest"
    else:
        raise RuntimeError(
            "CRITICAL: JWT_SECRET_KEY environment variable is missing! Production boots without an explicit environment secret are sealed."
        )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours
REFRESH_TOKEN_EXPIRE_DAYS = 7


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)


def create_access_token(
    data: Dict,
    expires_delta: Optional[timedelta] = None,
    tenant_id: Optional[int] = None,
) -> str:
    """Create JWT access token.

    If ``tenant_id`` is passed it is added as a top-level claim the tenant
    middleware reads on every request. Callers that already include
    ``tenant_id`` in ``data`` do not need to pass it separately.
    """
    to_encode = data.copy()
    if tenant_id is not None and "tenant_id" not in to_encode:
        to_encode["tenant_id"] = tenant_id

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update(
        {"exp": expire, "type": "refresh", "jti": secrets.token_urlsafe(32)}
    )
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict]:
    """Decode JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def verify_token(token: str, token_type: str = "access") -> Optional[Dict]:
    """Verify JWT token"""
    payload = decode_token(token)
    if payload is None:
        return None
    if payload.get("type") != token_type:
        return None
    exp = payload.get("exp")
    if exp is None:
        return None
    if datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
        return None
    return payload


def generate_password_reset_token() -> str:
    """Generate password reset token"""
    return secrets.token_urlsafe(32)


def get_current_active_user(token: str) -> Optional[Dict]:
    """Get current active user from token"""
    payload = verify_token(token)
    if payload is None:
        return None
    return payload
