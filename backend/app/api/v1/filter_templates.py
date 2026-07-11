"""Cross-entity filter template API."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db, require_role
from app.models import User
from app.models.filter_template import TemplateVisibility
from app.services.filter_template_service import FilterTemplateService

router = APIRouter(prefix="/filter-templates", tags=["Search — Filter Templates"])


def _serialize(t) -> dict:
    return {
        "id": t.id,
        "slug": t.slug,
        "name": t.name,
        "description": t.description,
        "primary_entity": t.primary_entity,
        "entity_types": t.entity_types,
        "filter_spec": t.filter_spec,
        "role_visibility": t.role_visibility,
        "visibility": t.visibility.value if t.visibility else None,
        "pinned_to": t.pinned_to,
        "is_system": t.is_system,
        "is_active": t.is_active,
        "use_count": t.use_count,
        "last_used_at": t.last_used_at.isoformat() if t.last_used_at else None,
        "created_by": t.created_by,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }


class TemplateIn(BaseModel):
    name: str = Field(..., min_length=2)
    description: Optional[str] = None
    primary_entity: str = Field(..., min_length=1)
    entity_types: Optional[List[str]] = None
    filter_spec: dict
    role_visibility: Optional[List[str]] = None
    visibility: TemplateVisibility = TemplateVisibility.PROPERTY
    pinned_to: Optional[List[str]] = None


class TemplateUpdateIn(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    entity_types: Optional[List[str]] = None
    filter_spec: Optional[dict] = None
    role_visibility: Optional[List[str]] = None
    visibility: Optional[TemplateVisibility] = None
    pinned_to: Optional[List[str]] = None
    is_active: Optional[bool] = None


class UseIn(BaseModel):
    entity_view: str = Field(..., min_length=1)


@router.get("")
def list_templates(
    primary_entity: Optional[str] = None,
    entity_view: Optional[str] = None,
    search: Optional[str] = Query(None, min_length=1),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows, total = FilterTemplateService(db).list(
        primary_entity=primary_entity,
        entity_view=entity_view,
        user_role=getattr(current_user, "role", None),
        search=search,
        limit=limit,
        offset=offset,
    )
    return {
        "items": [_serialize(r) for r in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/recent")
def recent(
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {
        "items": [
            _serialize(t)
            for t in FilterTemplateService(db).recent_for_user(current_user.id, limit=limit)
        ]
    }


@router.get("/{template_id}")
def get_template(
    template_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    t = FilterTemplateService(db).get(template_id)
    if not t:
        raise HTTPException(status_code=404, detail="Not found")
    return _serialize(t)


@router.post("", status_code=201)
def create_template(
    payload: TemplateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    t = FilterTemplateService(db).create(
        created_by=current_user.id, **payload.model_dump()
    )
    return _serialize(t)


@router.patch("/{template_id}")
def update_template(
    template_id: int,
    payload: TemplateUpdateIn,
    _: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    t = FilterTemplateService(db).update(
        template_id, **payload.model_dump(exclude_unset=True)
    )
    if not t:
        raise HTTPException(status_code=404, detail="Not found")
    return _serialize(t)


@router.delete("/{template_id}", status_code=204)
def delete_template(
    template_id: int,
    _: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    if not FilterTemplateService(db).delete(template_id):
        raise HTTPException(status_code=404, detail="Not found")


@router.post("/{template_id}/use")
def record_use(
    template_id: int,
    payload: UseIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    t = FilterTemplateService(db).record_use(
        template_id, user_id=current_user.id, entity_view=payload.entity_view
    )
    if not t:
        raise HTTPException(status_code=404, detail="Not found")
    return _serialize(t)
