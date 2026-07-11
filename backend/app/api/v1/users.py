from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import Optional, List
from app.api.dependencies import get_db, require_role
from app.services.user_management_service import UserManagementService
from app.models import User

router = APIRouter(prefix="/users", tags=["User Management"])


# =========================
# REQUEST / RESPONSE MODELS
# =========================


class UpdateUserRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None


class ResetPasswordRequest(BaseModel):
    new_password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    first_name: Optional[str]
    last_name: Optional[str]
    phone: Optional[str]
    is_active: bool
    is_superuser: bool
    failed_login_attempts: int
    last_login: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


# =========================
# USER MANAGEMENT
# =========================


@router.get("", summary="List users")
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    service = UserManagementService(db)

    result = service.get_users(
        skip=skip, limit=limit, role=role, is_active=is_active, search=search
    )

    return {
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "role": u.role,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "is_active": u.is_active,
                "is_superuser": u.is_superuser,
                "last_login": u.last_login.isoformat() if u.last_login else None,
                "created_at": u.created_at.isoformat(),
            }
            for u in result["users"]
        ],
        "total": result["total"],
        "skip": result["skip"],
        "limit": result["limit"],
    }


@router.get("/{user_id}", summary="Get user by ID")
async def get_user(
    user_id: int,
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    service = UserManagementService(db)
    user = service.get_user(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone": user.phone,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "failed_login_attempts": user.failed_login_attempts,
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "last_password_change": user.last_password_change.isoformat()
        if user.last_password_change
        else None,
        "created_at": user.created_at.isoformat(),
    }


@router.put("/{user_id}", summary="Update user")
async def update_user(
    user_id: int,
    update_data: UpdateUserRequest,
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    service = UserManagementService(db)

    try:
        user = service.update_user(
            user_id=user_id,
            updated_by=current_user.username,
            username=update_data.username,
            email=update_data.email,
            first_name=update_data.first_name,
            last_name=update_data.last_name,
            phone=update_data.phone,
            role=update_data.role,
        )

        return {
            "message": "User updated successfully",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
            },
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{user_id}/deactivate", summary="Deactivate user")
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    service = UserManagementService(db)

    try:
        user = service.deactivate_user(user_id, current_user.username)
        return {"message": f"User {user.username} deactivated successfully"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{user_id}/activate", summary="Activate user")
async def activate_user(
    user_id: int,
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    service = UserManagementService(db)

    try:
        user = service.activate_user(user_id, current_user.username)
        return {"message": f"User {user.username} activated successfully"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{user_id}/reset-password", summary="Reset user password (Admin)")
async def reset_password(
    user_id: int,
    reset_data: ResetPasswordRequest,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    service = UserManagementService(db)

    try:
        user = service.reset_password(
            user_id=user_id,
            new_password=reset_data.new_password,
            reset_by=current_user.username,
        )
        return {"message": f"Password reset successfully for {user.username}"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{user_id}/unlock", summary="Unlock user account")
async def unlock_account(
    user_id: int,
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    service = UserManagementService(db)

    try:
        user = service.unlock_account(user_id, current_user.username)
        return {"message": f"Account unlocked for {user.username}"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{user_id}/activity", summary="Get user activity")
async def get_user_activity(
    user_id: int,
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    service = UserManagementService(db)

    activities = service.get_user_activity(user_id, limit)

    return {
        "activities": [
            {
                "id": a.id,
                "action": a.action,
                "status": a.status,
                "details": a.details,
                "ip_address": a.ip_address,
                "created_at": a.created_at.isoformat(),
            }
            for a in activities
        ],
        "total": len(activities),
    }


@router.delete("/{user_id}", summary="Delete user")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    service = UserManagementService(db)
    try:
        service.delete_user(user_id, current_user.username)
        return {"message": "User deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}/stats", summary="Get user statistics")
async def get_user_stats(
    user_id: int,
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    service = UserManagementService(db)

    try:
        return service.get_user_stats(user_id)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/stats/roles", summary="Get role statistics")
async def get_role_stats(
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    service = UserManagementService(db)
    return service.get_role_stats()
