"""
Permission System - Role-based permissions
"""
from typing import List
from enum import Enum


class Role(str, Enum):
    """User roles"""

    ADMIN = "admin"
    MANAGER = "manager"
    FRONT_DESK = "front_desk"
    HOUSEKEEPER = "housekeeper"
    MAINTENANCE = "maintenance"
    ACCOUNTANT = "accountant"
    STAFF = "staff"


class Permission(str, Enum):
    """System permissions"""

    # Dashboard
    VIEW_DASHBOARD = "view_dashboard"

    # Reservations
    VIEW_RESERVATIONS = "view_reservations"
    CREATE_RESERVATION = "create_reservation"
    MODIFY_RESERVATION = "modify_reservation"
    CANCEL_RESERVATION = "cancel_reservation"

    # Check-in/out
    CHECK_IN = "check_in"
    CHECK_OUT = "check_out"

    # Guests
    VIEW_GUESTS = "view_guests"
    CREATE_GUEST = "create_guest"
    MODIFY_GUEST = "modify_guest"
    DELETE_GUEST = "delete_guest"

    # Rooms
    VIEW_ROOMS = "view_rooms"
    MODIFY_ROOMS = "modify_rooms"
    DELETE_ROOMS = "delete_rooms"

    # Charges & Payments
    VIEW_CHARGES = "view_charges"
    CREATE_CHARGE = "create_charge"
    MODIFY_CHARGE = "modify_charge"
    DELETE_CHARGE = "delete_charge"
    VIEW_PAYMENTS = "view_payments"
    CREATE_PAYMENT = "create_payment"

    # Housekeeping
    VIEW_HOUSEKEEPING = "view_housekeeping"
    ASSIGN_HOUSEKEEPING = "assign_housekeeping"
    COMPLETE_TASK = "complete_task"
    INSPECT_TASK = "inspect_task"

    # Maintenance
    VIEW_MAINTENANCE = "view_maintenance"
    CREATE_MAINTENANCE = "create_maintenance"
    COMPLETE_MAINTENANCE = "complete_maintenance"

    # Rates
    VIEW_RATES = "view_rates"
    MODIFY_RATES = "modify_rates"

    # Reports & Analytics
    VIEW_REPORTS = "view_reports"
    VIEW_ANALYTICS = "view_analytics"
    EXPORT_DATA = "export_data"

    # User Management
    VIEW_USERS = "view_users"
    CREATE_USER = "create_user"
    MODIFY_USER = "modify_user"
    DELETE_USER = "delete_user"

    # Settings
    VIEW_SETTINGS = "view_settings"
    MODIFY_SETTINGS = "modify_settings"


# Role to Permission Mapping
ROLE_PERMISSIONS = {
    Role.ADMIN: ["*"],  # All permissions
    Role.MANAGER: [
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_RESERVATIONS,
        Permission.CREATE_RESERVATION,
        Permission.MODIFY_RESERVATION,
        Permission.CANCEL_RESERVATION,
        Permission.CHECK_IN,
        Permission.CHECK_OUT,
        Permission.VIEW_GUESTS,
        Permission.CREATE_GUEST,
        Permission.MODIFY_GUEST,
        Permission.VIEW_ROOMS,
        Permission.MODIFY_ROOMS,
        Permission.VIEW_CHARGES,
        Permission.CREATE_CHARGE,
        Permission.MODIFY_CHARGE,
        Permission.VIEW_PAYMENTS,
        Permission.CREATE_PAYMENT,
        Permission.VIEW_HOUSEKEEPING,
        Permission.ASSIGN_HOUSEKEEPING,
        Permission.INSPECT_TASK,
        Permission.VIEW_MAINTENANCE,
        Permission.CREATE_MAINTENANCE,
        Permission.VIEW_RATES,
        Permission.MODIFY_RATES,
        Permission.VIEW_REPORTS,
        Permission.VIEW_ANALYTICS,
        Permission.EXPORT_DATA,
        Permission.VIEW_USERS,
        Permission.CREATE_USER,
        Permission.VIEW_SETTINGS,
    ],
    Role.FRONT_DESK: [
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_RESERVATIONS,
        Permission.CREATE_RESERVATION,
        Permission.MODIFY_RESERVATION,
        Permission.CHECK_IN,
        Permission.CHECK_OUT,
        Permission.VIEW_GUESTS,
        Permission.CREATE_GUEST,
        Permission.MODIFY_GUEST,
        Permission.VIEW_ROOMS,
        Permission.VIEW_CHARGES,
        Permission.CREATE_CHARGE,
        Permission.VIEW_PAYMENTS,
        Permission.CREATE_PAYMENT,
        Permission.VIEW_HOUSEKEEPING,
    ],
    Role.HOUSEKEEPER: [
        Permission.VIEW_HOUSEKEEPING,
        Permission.COMPLETE_TASK,
        Permission.VIEW_MAINTENANCE,
    ],
    Role.MAINTENANCE: [
        Permission.VIEW_MAINTENANCE,
        Permission.COMPLETE_MAINTENANCE,
        Permission.VIEW_HOUSEKEEPING,
    ],
    Role.ACCOUNTANT: [
        Permission.VIEW_CHARGES,
        Permission.VIEW_PAYMENTS,
        Permission.VIEW_REPORTS,
        Permission.VIEW_ANALYTICS,
        Permission.EXPORT_DATA,
    ],
    Role.STAFF: [
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_RESERVATIONS,
        Permission.VIEW_GUESTS,
    ],
}


def get_role_permissions(role: str) -> List[str]:
    """
    Get permissions for a role

    Args:
        role: User role

    Returns:
        List of permissions
    """
    return ROLE_PERMISSIONS.get(role, [])


def has_permission(user_role: str, permission: str, is_superuser: bool = False) -> bool:
    """
    Check if user has permission

    Args:
        user_role: User role
        permission: Required permission
        is_superuser: Is user superuser

    Returns:
        True if has permission
    """
    if is_superuser:
        return True

    permissions = get_role_permissions(user_role)

    if "*" in permissions:
        return True

    return permission in permissions
