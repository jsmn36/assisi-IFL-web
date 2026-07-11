"""
FilterService
Advanced filtering with dynamic conditions
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import Date, String, and_, cast, func, not_, or_
from sqlalchemy.orm import Query, Session

from app.models import Guest, Reservation, Room, User
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class FilterService(BaseService):
    """
    Service for advanced filtering

    Methods:
    - apply_filters: Apply filters to query
    - build_filter_condition: Build filter condition
    - get_filter_operators: Get available operators
    - validate_filter: Validate filter
    - get_filterable_fields: Get filterable fields for entity
    """

    OPERATORS = {
        "equals": lambda field, value: field == value,
        "not_equals": lambda field, value: field != value,
        "contains": lambda field, value: field.ilike(f"%{value}%"),
        "not_contains": lambda field, value: not_(field.ilike(f"%{value}%")),
        "starts_with": lambda field, value: field.ilike(f"{value}%"),
        "ends_with": lambda field, value: field.ilike(f"%{value}"),
        "greater_than": lambda field, value: field > value,
        "greater_than_or_equal": lambda field, value: field >= value,
        "less_than": lambda field, value: field < value,
        "less_than_or_equal": lambda field, value: field <= value,
        "in": lambda field, value: field.in_(
            value if isinstance(value, list) else [value]
        ),
        "not_in": lambda field, value: not_(
            field.in_(value if isinstance(value, list) else [value])
        ),
        "is_null": lambda field, value: field.is_(None),
        "is_not_null": lambda field, value: field.isnot(None),
        "between": lambda field, value: and_(field >= value[0], field <= value[1])
        if isinstance(value, list) and len(value) == 2
        else True,
    }

    def apply_filters(
        self, query: Query, model: Any, filters: List[Dict], logic: str = "and"
    ) -> Query:
        """Apply filters to query"""
        if not filters:
            return query

        conditions = []
        for filter_config in filters:
            condition = self.build_filter_condition(model, filter_config)
            if condition is not None:
                conditions.append(condition)

        if not conditions:
            return query

        if logic == "or":
            return query.filter(or_(*conditions))
        else:
            return query.filter(and_(*conditions))

    def build_filter_condition(self, model: Any, filter_config: Dict) -> Optional[Any]:
        """Build filter condition"""
        field_name = filter_config.get("field")
        operator = filter_config.get("operator", "equals")
        value = filter_config.get("value")

        if not field_name or not hasattr(model, field_name):
            return None

        field = getattr(model, field_name)
        operator_func = self.OPERATORS.get(operator)
        if not operator_func:
            return None

        if operator in ["is_null", "is_not_null"]:
            return operator_func(field, None)

        try:
            return operator_func(field, value)
        except Exception:
            logger.exception(
                "Filter error for field=%s operator=%s", field_name, operator
            )
            return None

    def get_filter_operators(self) -> List[Dict]:
        """Get available filter operators"""
        return [
            {
                "value": "equals",
                "label": "Equals",
                "types": ["string", "number", "boolean", "date"],
            },
            {
                "value": "not_equals",
                "label": "Not Equals",
                "types": ["string", "number", "boolean", "date"],
            },
            {"value": "contains", "label": "Contains", "types": ["string"]},
            {"value": "not_contains", "label": "Does Not Contain", "types": ["string"]},
            {"value": "starts_with", "label": "Starts With", "types": ["string"]},
            {"value": "ends_with", "label": "Ends With", "types": ["string"]},
            {
                "value": "greater_than",
                "label": "Greater Than",
                "types": ["number", "date"],
            },
            {
                "value": "greater_than_or_equal",
                "label": "Greater Than or Equal",
                "types": ["number", "date"],
            },
            {"value": "less_than", "label": "Less Than", "types": ["number", "date"]},
            {
                "value": "less_than_or_equal",
                "label": "Less Than or Equal",
                "types": ["number", "date"],
            },
            {"value": "in", "label": "In", "types": ["string", "number"]},
            {"value": "not_in", "label": "Not In", "types": ["string", "number"]},
            {
                "value": "is_null",
                "label": "Is Empty",
                "types": ["string", "number", "date"],
            },
            {
                "value": "is_not_null",
                "label": "Is Not Empty",
                "types": ["string", "number", "date"],
            },
            {"value": "between", "label": "Between", "types": ["number", "date"]},
        ]

    def validate_filter(self, model: Any, filter_config: Dict) -> Dict:
        """Validate filter configuration"""
        errors = []

        field_name = filter_config.get("field")
        if not field_name:
            errors.append("Field is required")
        elif not hasattr(model, field_name):
            errors.append(f"Field '{field_name}' does not exist")

        operator = filter_config.get("operator")
        if not operator:
            errors.append("Operator is required")
        elif operator not in self.OPERATORS:
            errors.append(f"Invalid operator '{operator}'")

        if operator not in ["is_null", "is_not_null"]:
            value = filter_config.get("value")
            if value is None and operator != "equals":
                errors.append("Value is required")

        return {"valid": len(errors) == 0, "errors": errors}

    def get_filterable_fields(self, entity_type: str) -> List[Dict]:
        """Get filterable fields for entity"""
        fields_map = {
            "reservation": [
                {
                    "name": "confirmation_code",
                    "label": "Confirmation Code",
                    "type": "string",
                },
                {"name": "guest_name", "label": "Guest Name", "type": "string"},
                {"name": "guest_email", "label": "Guest Email", "type": "string"},
                {"name": "guest_phone", "label": "Guest Phone", "type": "string"},
                {"name": "room_number", "label": "Room Number", "type": "string"},
                {
                    "name": "status",
                    "label": "Status",
                    "type": "string",
                    "options": [
                        "pending",
                        "confirmed",
                        "checked_in",
                        "checked_out",
                        "cancelled",
                    ],
                },
                {"name": "check_in_date", "label": "Check-in Date", "type": "date"},
                {"name": "check_out_date", "label": "Check-out Date", "type": "date"},
                {"name": "total_amount", "label": "Total Amount", "type": "number"},
                {
                    "name": "number_of_guests",
                    "label": "Number of Guests",
                    "type": "number",
                },
                {"name": "created_at", "label": "Created Date", "type": "date"},
            ],
            "guest": [
                {"name": "first_name", "label": "First Name", "type": "string"},
                {"name": "last_name", "label": "Last Name", "type": "string"},
                {"name": "email", "label": "Email", "type": "string"},
                {"name": "phone", "label": "Phone", "type": "string"},
                {
                    "name": "guest_type",
                    "label": "Guest Type",
                    "type": "string",
                    "options": ["individual", "corporate", "group"],
                },
                {"name": "country", "label": "Country", "type": "string"},
                {
                    "name": "passport_number",
                    "label": "Passport Number",
                    "type": "string",
                },
                {"name": "id_number", "label": "ID Number", "type": "string"},
                {"name": "created_at", "label": "Created Date", "type": "date"},
            ],
            "room": [
                {"name": "room_number", "label": "Room Number", "type": "string"},
                {
                    "name": "room_type",
                    "label": "Room Type",
                    "type": "string",
                    "options": ["standard", "deluxe", "suite", "presidential"],
                },
                {
                    "name": "status",
                    "label": "Status",
                    "type": "string",
                    "options": [
                        "available",
                        "occupied",
                        "maintenance",
                        "out_of_service",
                    ],
                },
                {"name": "floor", "label": "Floor", "type": "number"},
                {"name": "max_occupancy", "label": "Max Occupancy", "type": "number"},
                {"name": "base_price", "label": "Base Price", "type": "number"},
            ],
            "user": [
                {"name": "username", "label": "Username", "type": "string"},
                {"name": "email", "label": "Email", "type": "string"},
                {"name": "first_name", "label": "First Name", "type": "string"},
                {"name": "last_name", "label": "Last Name", "type": "string"},
                {
                    "name": "role",
                    "label": "Role",
                    "type": "string",
                    "options": [
                        "admin",
                        "manager",
                        "front_desk",
                        "housekeeper",
                        "maintenance",
                        "accountant",
                        "staff",
                    ],
                },
                {"name": "is_active", "label": "Is Active", "type": "boolean"},
                {"name": "created_at", "label": "Created Date", "type": "date"},
            ],
        }

        return fields_map.get(entity_type, [])
