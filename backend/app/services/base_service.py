import logging
from typing import Any, Optional, Type, TypeVar

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ServiceError(Exception):
    def __init__(
        self, message: str, details: Optional[dict] = None, code: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.code = code or self.__class__.__name__


class ValidationError(ServiceError):
    pass


class NotFoundError(ServiceError):
    pass


class BusinessRuleError(ServiceError):
    pass


class BaseService:
    def __init__(self, db: Session):
        self.db = db

    def commit(self):
        try:
            self.db.commit()
        except SQLAlchemyError as e:
            self.db.rollback()
            raise ServiceError(f"Database error: {str(e)}")

    def refresh(self, instance: Any):
        self.db.refresh(instance)

    def get_or_404(self, model: Type[T], id: Any) -> T:
        instance = self.db.query(model).get(id)
        if not instance:
            raise NotFoundError(f"{model.__name__} with id {id} not found")
        return instance

    def _log_action(
        self, action: str, entity_type: str, entity_id: Any, details: Any = None
    ):
        """Record an audit entry for a service-level action.

        Attempts to persist via the shared write_audit helper so the log
        survives process restart; falls back to logging-only if the audit
        helper cannot run (e.g. session misconfigured).

        ``details`` is coerced to str — many call sites pass model
        instances (e.g. the acting User) which SQLAlchemy cannot bind to a
        Text column.
        """
        details_str = None if details is None else str(details)
        try:
            from app.services.audit_helper import write_audit

            write_audit(
                self.db,
                action=action,
                resource_type=entity_type,
                resource_id=entity_id if isinstance(entity_id, int) else None,
                details=details_str,
            )
        except Exception:
            logger.info(
                "audit_fallback action=%s entity=%s:%s details=%s",
                action,
                entity_type,
                entity_id,
                details_str or "",
            )
