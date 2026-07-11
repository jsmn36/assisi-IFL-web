"""
Permission Management API Endpoints
"""
from fastapi import APIRouter, Depends
from typing import List, Dict
from app.api.dependencies import require_role
from app.models import User
from app.core.permissions import (
    Role,
    Permission,
    ROLE_PERMISSIONS,
    get_role_permissions,
)

router = APIRouter(prefix="/permissions", tags=["Permissions"])


@router.get("/roles", summary="Get all roles")

# === Permissions ===
@router.get("/roles", summary="Get all roles")
async def get_roles(current_user: User = Depends(require_role("admin", "manager"))):
    """Get all available roles"""
    return {
        "roles": [
            {
                "name": role.value,
                "display_name": role.value.replace("_", " ").title(),
                "permission_count": len(get_role_permissions(role.value)),
            }
            for role in Role
        ]
    }


@router.get("/all", summary="Get all permissions")
async def get_all_permissions(
    current_user: User = Depends(require_role("admin", "manager"))
):
    """Get all available permissions"""
    permissions_by_category = {
        "Dashboard": [],
        "Reservations": [],
        "Check-in/out": [],
        "Guests": [],
        "Rooms": [],
        "Charges & Payments": [],
        "Housekeeping": [],
        "Maintenance": [],
        "Rates": [],
        "Reports & Analytics": [],
        "User Management": [],
        "Settings": [],
    }

    for perm in Permission:
        display_name = perm.value.replace("_", " ").title()
        if "dashboard" in perm.value:
            category = "Dashboard"
        elif (
            "reservation" in perm.value
            or "check_in" in perm.value
            or "check_out" in perm.value
        ):
            category = "Reservations" if "reservation" in perm.value else "Check-in/out"
        elif "guest" in perm.value:
            category = "Guests"
        elif "room" in perm.value:
            category = "Rooms"
        elif "charge" in perm.value or "payment" in perm.value:
            category = "Charges & Payments"
        elif "housekeeping" in perm.value or "task" in perm.value:
            category = "Housekeeping"
        elif "maintenance" in perm.value:
            category = "Maintenance"
        elif "rate" in perm.value:
            category = "Rates"
        elif (
            "report" in perm.value
            or "analytics" in perm.value
            or "export" in perm.value
        ):
            category = "Reports & Analytics"
        elif "user" in perm.value:
            category = "User Management"
        elif "settings" in perm.value:
            category = "Settings"
        else:
            category = "Dashboard"
        permissions_by_category[category].append(
            {"name": perm.value, "display_name": display_name}
        )

    return {"categories": permissions_by_category, "total": len(Permission)}


@router.get("/role/{role}", summary="Get permissions for role")
async def get_role_permissions_endpoint(
    role: str, current_user: User = Depends(require_role("admin", "manager"))
):
    """Get permissions for a specific role"""
    permissions = get_role_permissions(role)
    if not permissions:
        return {"role": role, "permissions": [], "has_all": False}
    return {
        "role": role,
        "permissions": permissions,
        "has_all": "*" in permissions,
        "count": len(permissions),
    }


@router.get("/matrix", summary="Get permission matrix")
async def get_permission_matrix(current_user: User = Depends(require_role("admin"))):
    """Get complete permission matrix (Admin only)"""
    matrix = []
    for role in Role:
        role_perms = get_role_permissions(role.value)
        has_all = "*" in role_perms


@router.get("/all", summary="Get all permissions")
async def get_all_permissions(
    current_user: User = Depends(require_role("admin", "manager"))
):
    """Get all available permissions"""
    permissions_by_category = {
        "Dashboard": [],
        "Reservations": [],
        "Check-in/out": [],
        "Guests": [],
        "Rooms": [],
        "Charges & Payments": [],
        "Housekeeping": [],
        "Maintenance": [],
        "Rates": [],
        "Reports & Analytics": [],
        "User Management": [],
        "Settings": [],
    }

    for perm in Permission:
        display_name = perm.value.replace("_", " ").title()

        if "dashboard" in perm.value:
            category = "Dashboard"
        elif (
            "reservation" in perm.value
            or "check_in" in perm.value
            or "check_out" in perm.value
        ):
            category = "Reservations" if "reservation" in perm.value else "Check-in/out"
        elif "guest" in perm.value:
            category = "Guests"
        elif "room" in perm.value:
            category = "Rooms"
        elif "charge" in perm.value or "payment" in perm.value:
            category = "Charges & Payments"
        elif "housekeeping" in perm.value or "task" in perm.value:
            category = "Housekeeping"
        elif "maintenance" in perm.value:
            category = "Maintenance"
        elif "rate" in perm.value:
            category = "Rates"
        elif (
            "report" in perm.value
            or "analytics" in perm.value
            or "export" in perm.value
        ):
            category = "Reports & Analytics"
        elif "user" in perm.value:
            category = "User Management"
        elif "settings" in perm.value:
            category = "Settings"
        else:
            category = "Dashboard"

        permissions_by_category[category].append(
            {"name": perm.value, "display_name": display_name}
        )

    return {"categories": permissions_by_category, "total": len(Permission)}


@router.get("/role/{role}", summary="Get permissions for role")
async def get_role_permissions_endpoint(
    role: str, current_user: User = Depends(require_role("admin", "manager"))
):
    """Get permissions for a specific role"""
    permissions = get_role_permissions(role)

    if not permissions:
        return {"role": role, "permissions": [], "has_all": False}

    return {
        "role": role,
        "permissions": permissions,
        "has_all": "*" in permissions,
        "count": len(permissions),
    }


@router.get("/matrix", summary="Get permission matrix")
async def get_permission_matrix(current_user: User = Depends(require_role("admin"))):
    """Get complete permission matrix (Admin only)"""
    matrix = []

    for role in Role:
        role_perms = get_role_permissions(role.value)
        has_all = "*" in role_perms

        matrix.append(
            {
                "role": role.value,
                "display_name": role.value.replace("_", " ").title(),
                "has_all_permissions": has_all,
                "permissions": role_perms if not has_all else ["*"],
                "permission_count": len(role_perms),
            }
        )

    return {
        "matrix": matrix,
        "total_roles": len(Role),
        "total_permissions": len(Permission),
    }
