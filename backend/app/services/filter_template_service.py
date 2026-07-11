"""Cross-entity filter template service."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable, List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.filter_template import (
    FilterTemplate,
    FilterTemplateUse,
    TemplateVisibility,
)


def _slugify(name: str) -> str:
    base = "".join(c.lower() if c.isalnum() else "-" for c in name).strip("-")
    while "--" in base:
        base = base.replace("--", "-")
    return base[:120] or "template"


class FilterTemplateService:
    def __init__(self, db: Session):
        self.db = db

    # ---------- CRUD ----------

    def list(
        self,
        primary_entity: Optional[str] = None,
        entity_view: Optional[str] = None,
        user_role: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[FilterTemplate], int]:
        q = self.db.query(FilterTemplate).filter(FilterTemplate.is_active.is_(True))
        if primary_entity:
            q = q.filter(FilterTemplate.primary_entity == primary_entity)
        if search:
            term = f"%{search.lower()}%"
            q = q.filter(
                or_(
                    FilterTemplate.name.ilike(term),
                    FilterTemplate.description.ilike(term),
                    FilterTemplate.slug.ilike(term),
                )
            )
        # If entity_view is given, restrict to templates that mention it.
        rows = q.order_by(FilterTemplate.use_count.desc(), FilterTemplate.name).all()
        if entity_view:
            rows = [r for r in rows if entity_view in (r.entity_types or [])]
        if user_role:
            rows = [
                r
                for r in rows
                if not r.role_visibility or user_role in (r.role_visibility or [])
            ]
        total = len(rows)
        return rows[offset : offset + limit], total

    def get(self, template_id: int) -> Optional[FilterTemplate]:
        return (
            self.db.query(FilterTemplate)
            .filter(FilterTemplate.id == template_id)
            .first()
        )

    def get_by_slug(self, slug: str) -> Optional[FilterTemplate]:
        return (
            self.db.query(FilterTemplate)
            .filter(FilterTemplate.slug == slug)
            .first()
        )

    def create(
        self,
        *,
        name: str,
        primary_entity: str,
        filter_spec: dict,
        description: Optional[str] = None,
        entity_types: Optional[List[str]] = None,
        role_visibility: Optional[List[str]] = None,
        visibility: TemplateVisibility = TemplateVisibility.PROPERTY,
        pinned_to: Optional[List[str]] = None,
        is_system: bool = False,
        created_by: Optional[int] = None,
    ) -> FilterTemplate:
        slug_base = _slugify(name)
        slug = slug_base
        n = 1
        while self.db.query(FilterTemplate).filter(FilterTemplate.slug == slug).first():
            n += 1
            slug = f"{slug_base}-{n}"
        t = FilterTemplate(
            slug=slug,
            name=name,
            description=description,
            primary_entity=primary_entity,
            entity_types=entity_types or [primary_entity],
            filter_spec=filter_spec,
            role_visibility=role_visibility or [],
            visibility=visibility,
            pinned_to=pinned_to or [],
            is_system=is_system,
            created_by=created_by,
        )
        self.db.add(t)
        self.db.commit()
        self.db.refresh(t)
        return t

    def update(
        self, template_id: int, **fields
    ) -> Optional[FilterTemplate]:
        t = self.get(template_id)
        if not t:
            return None
        for k, v in fields.items():
            if v is None:
                continue
            setattr(t, k, v)
        self.db.commit()
        self.db.refresh(t)
        return t

    def delete(self, template_id: int) -> bool:
        t = self.get(template_id)
        if not t:
            return False
        if t.is_system:
            t.is_active = False
            self.db.commit()
            return True
        self.db.delete(t)
        self.db.commit()
        return True

    # ---------- usage ----------

    def record_use(
        self,
        template_id: int,
        user_id: int,
        entity_view: str,
    ) -> Optional[FilterTemplate]:
        t = self.get(template_id)
        if not t:
            return None
        self.db.add(
            FilterTemplateUse(
                template_id=template_id,
                user_id=user_id,
                entity_view=entity_view,
            )
        )
        t.use_count = (t.use_count or 0) + 1
        t.last_used_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(t)
        return t

    def recent_for_user(self, user_id: int, limit: int = 5) -> List[FilterTemplate]:
        rows = (
            self.db.query(FilterTemplate)
            .join(FilterTemplateUse, FilterTemplateUse.template_id == FilterTemplate.id)
            .filter(FilterTemplateUse.user_id == user_id)
            .filter(FilterTemplate.is_active.is_(True))
            .order_by(FilterTemplateUse.used_at.desc())
            .limit(limit * 4)
            .all()
        )
        # de-dupe preserving order
        seen = set()
        out: List[FilterTemplate] = []
        for r in rows:
            if r.id in seen:
                continue
            seen.add(r.id)
            out.append(r)
            if len(out) >= limit:
                break
        return out
