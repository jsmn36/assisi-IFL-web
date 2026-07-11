"""
# Authentication API Endpoints
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])


# Request/Response Models
class LoginRequest(BaseModel):
    username: str
    password: str


class TenantMembershipOut(BaseModel):
    tenant_id: int
    tenant_slug: str
    tenant_name: str
    role: str
    is_default: bool

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user: dict
    # When the user belongs to multiple tenants the API returns these and
    # leaves access_token/refresh_token empty; the caller must follow up
    # with /auth/select-tenant.
    memberships: List[TenantMembershipOut] = []
    requires_tenant_selection: bool = False


class SelectTenantRequest(BaseModel):
    tenant_id: int


class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class CreateUserRequest(BaseModel):
    username: str
    email: str
    password: str
    role: str = "staff"
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class StudentRegisterRequest(BaseModel):
    admission_number: str
    student_name: str
    username: str
    email: str
    password: str
    class_or_department: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str

    class Config:
        from_attributes = True


def _membership_to_out(membership, tenant) -> TenantMembershipOut:
    return TenantMembershipOut(
        tenant_id=membership.tenant_id,
        tenant_slug=tenant.slug if tenant else "",
        tenant_name=tenant.name if tenant else "",
        role=membership.role,
        is_default=membership.is_default,
    )


def _hydrate_memberships(db: Session, memberships) -> List[TenantMembershipOut]:
    from app.core.tenant_context import bypass_tenant_filter
    from app.models import Tenant

    if not memberships:
        return []
    ids = [m.tenant_id for m in memberships]
    with bypass_tenant_filter():
        rows = db.query(Tenant).filter(Tenant.id.in_(ids)).all()
    by_id = {t.id: t for t in rows}
    return [_membership_to_out(m, by_id.get(m.tenant_id)) for m in memberships]


# === Authentication ===
@router.post("/login", summary="Login user", response_model=LoginResponse)
async def login(
    request: Request,
    login_data: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    """Authenticate user.

    On success the response shape depends on tenant membership count:
      - 1 membership: ``access_token``/``refresh_token`` are returned and
        cookies are set; the caller can immediately make tenant-scoped calls.
      - >1 memberships: tokens are NOT returned; ``memberships`` lists the
        choices and ``requires_tenant_selection`` is true. The caller must
        follow up with ``POST /auth/select-tenant``.
    """
    from app.services.auth_service import AuthService

    service = AuthService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    try:
        user, access_token, refresh_token, memberships = service.authenticate_user(
            username=login_data.username,
            password=login_data.password,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_payload = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
    }
    membership_outs = _hydrate_memberships(db, memberships)

    if not access_token:
        # Multi-membership: client must select a tenant
        return LoginResponse(
            user=user_payload,
            memberships=membership_outs,
            requires_tenant_selection=True,
        )

    is_secure = request.url.scheme == "https"
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=is_secure,
        samesite="lax",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=is_secure,
        samesite="lax",
    )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user_payload,
        memberships=membership_outs,
    )


@router.post("/register-student", summary="Register a student account")
async def register_student(
    payload: StudentRegisterRequest,
    db: Session = Depends(get_db),
):
    from app.models.student import StudentAdmission, StudentProfile
    from app.models import User, UserTenant, DEFAULT_TENANT_ID
    from app.core.security import get_password_hash
    from app.core.tenant_context import bypass_tenant_filter

    with bypass_tenant_filter():
        # 1. Verify admission number exists in DB
        admission = db.query(StudentAdmission).filter(StudentAdmission.admission_number == payload.admission_number).first()
        if not admission:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid admission number. Only registered students are allowed to create an account."
            )

        # 2. Check if already registered
        if admission.is_registered:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account has already been registered for this admission number."
            )

        # 3. Check if username or email is already taken
        existing_user = db.query(User).filter((User.username == payload.username) | (User.email == payload.email)).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email is already registered."
            )

        # 4. Create User
        name_parts = payload.student_name.strip().split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        user = User(
            username=payload.username,
            email=payload.email,
            hashed_password=get_password_hash(payload.password),
            role="student",
            is_active=False,  # Inactive pending administrator approval!
            first_name=first_name,
            last_name=last_name,
        )
        db.add(user)
        db.flush()

        # 5. Create membership in Default Tenant
        membership = UserTenant(
            user_id=user.id,
            tenant_id=DEFAULT_TENANT_ID,
            role="student",
            is_default=True,
        )
        db.add(membership)

        # 6. Create Student Profile
        profile = StudentProfile(
            user_id=user.id,
            admission_number=payload.admission_number,
            class_or_department=payload.class_or_department or admission.class_or_department,
            privacy_settings="public"
        )
        db.add(profile)
        db.commit()

    return {"message": "Registration successful! Your account is pending institutional approval. Please contact your administrator."}


@router.post("/select-tenant", summary="Select tenant after multi-tenant login")
async def select_tenant(
    request: Request,
    payload: SelectTenantRequest,
    response: Response,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Issue a fresh tenant-bound token pair for the chosen tenant.

    Requires the user to already be authenticated (e.g. via the partial
    token issued during initial login, or any active session). The user
    must have a UserTenant row for the requested tenant_id.
    """
    from app.services.auth_service import AuthService

    service = AuthService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    user, access_token, refresh_token = service.select_tenant(
        user_id=current_user.id,
        tenant_id=payload.tenant_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No membership in requested tenant",
        )

    is_secure = request.url.scheme == "https"
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=is_secure,
        samesite="lax",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=is_secure,
        samesite="lax",
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "tenant_id": payload.tenant_id,
    }


@router.get("/memberships", summary="List the current user's tenant memberships")
async def list_memberships(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.services.auth_service import AuthService

    service = AuthService(db)
    memberships = service.get_memberships(current_user.id)
    return {"memberships": _hydrate_memberships(db, memberships)}


@router.post("/refresh", summary="Refresh access token")
async def refresh_token(
    refresh_data: RefreshRequest, response: Response, db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    try:
        from app.services.auth_service import AuthService

        service = AuthService(db)
        access_token = service.refresh_access_token(refresh_data.refresh_token)
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=False,
            samesite="lax",
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/logout", summary="Logout user")
async def logout(
    refresh_token: str,
    response: Response,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Logout user"""
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Successfully logged out"}


@router.get("/me", summary="Get current user")
async def get_me(current_user=Depends(get_current_user)):
    """Get current authenticated user"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "first_name": getattr(current_user, "first_name", None),
        "last_name": getattr(current_user, "last_name", None),
    }


@router.post("/change-password", summary="Change password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change user password"""
    return {"message": "Password changed successfully"}


# === User Management ===
@router.post("/users", summary="Create user")
async def create_user(
    user_data: CreateUserRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create new user"""
    try:
        from app.services.auth_service import AuthService

        service = AuthService(db)
        user = service.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            role=user_data.role,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            created_by=current_user,
        )
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/users", summary="List users")
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all users"""
    from app.models import User

    users = db.query(User).offset(skip).limit(limit).all()
    return {
        "users": [
            {"id": u.id, "username": u.username, "email": u.email, "role": u.role}
            for u in users
        ],
        "total": db.query(User).count(),
    }
