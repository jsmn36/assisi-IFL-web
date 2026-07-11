from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, cast, String, desc
from app.services.base_service import BaseService
from app.models import (
    Reservation,
    Guest,
    Room,
    User,
    SavedSearch,
    SearchHistory,
    QuickFilter,
)


class SearchService(BaseService):
    """
    Service for global search
    """

    def __init__(self, db: Session):
        self.db = db

    # =========================
    # GLOBAL SEARCH
    # =========================
    def global_search(
        self,
        query: str,
        user_id: int,
        entities: Optional[List[str]] = None,
        limit: int = 20,
    ) -> Dict:
        if not query or len(query) < 2:
            return {"results": {}, "total": 0}

        entities = entities or ["reservations", "guests", "rooms", "users"]

        results = {}
        total = 0

        if "reservations" in entities:
            data = self.search_reservations(query, limit=limit)
            if data:
                results["reservations"] = data
                total += len(data)

        if "guests" in entities:
            data = self.search_guests(query, limit=limit)
            if data:
                results["guests"] = data
                total += len(data)

        if "rooms" in entities:
            data = self.search_rooms(query, limit=limit)
            if data:
                results["rooms"] = data
                total += len(data)

        if "users" in entities:
            data = self.search_users(query, limit=limit)
            if data:
                results["users"] = data
                total += len(data)

        # Track search
        self.track_search(
            user_id=user_id, entity_type="global", search_term=query, result_count=total
        )

        return {"query": query, "results": results, "total": total}

    # =========================
    # RESERVATIONS
    # =========================
    def search_reservations(
        self,
        query: str,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 20,
    ) -> List[Reservation]:
        filters = []

        if query:
            pattern = f"%{query}%"
            filters.append(
                or_(
                    Reservation.confirmation_number.ilike(pattern),
                    Guest.first_name.ilike(pattern),
                    Guest.last_name.ilike(pattern),
                    Guest.email.ilike(pattern),
                    Guest.phone.ilike(pattern),
                )
            )

        if status:
            filters.append(Reservation.status == status)

        if start_date:
            filters.append(Reservation.check_in_date >= start_date)

        if end_date:
            filters.append(Reservation.check_out_date <= end_date)

        q = self.db.query(Reservation)

        if filters:
            q = q.filter(and_(*filters))

        return q.order_by(Reservation.created_at.desc()).limit(limit).all()

    # =========================
    # GUESTS
    # =========================
    def search_guests(
        self, query: str, guest_type: Optional[str] = None, limit: int = 20
    ) -> List[Guest]:
        filters = []

        if query:
            pattern = f"%{query}%"
            filters.append(
                or_(
                    Guest.first_name.ilike(pattern),
                    Guest.last_name.ilike(pattern),
                    Guest.email.ilike(pattern),
                    Guest.phone.ilike(pattern),
                    Guest.passport_number.ilike(pattern),
                    Guest.id_number.ilike(pattern),
                )
            )

        if guest_type:
            filters.append(Guest.guest_type == guest_type)

        q = self.db.query(Guest)

        if filters:
            q = q.filter(and_(*filters))

        return q.order_by(Guest.created_at.desc()).limit(limit).all()

    # =========================
    # ROOMS
    # =========================
    def search_rooms(
        self,
        query: str,
        room_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
    ) -> List[Room]:
        filters = []

        if query:
            pattern = f"%{query}%"
            filters.append(
                or_(
                    Room.room_number.ilike(pattern),
                    cast(Room.floor, String).ilike(pattern),
                )
            )

        if room_type:
            filters.append(Room.room_type == room_type)

        if status:
            filters.append(Room.status == status)

        q = self.db.query(Room)

        if filters:
            q = q.filter(and_(*filters))

        return q.order_by(Room.room_number).limit(limit).all()

    # =========================
    # USERS
    # =========================
    def search_users(
        self,
        query: str,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 20,
    ) -> List[User]:
        filters = []

        if query:
            pattern = f"%{query}%"
            filters.append(
                or_(
                    User.username.ilike(pattern),
                    User.email.ilike(pattern),
                    User.first_name.ilike(pattern),
                    User.last_name.ilike(pattern),
                )
            )

        if role:
            filters.append(User.role == role)

        if is_active is not None:
            filters.append(User.is_active.is_(is_active))

        q = self.db.query(User)

        if filters:
            q = q.filter(and_(*filters))

        return q.order_by(User.created_at.desc()).limit(limit).all()

    # =========================
    # SAVED SEARCH
    # =========================
    def save_search(
        self,
        user_id: int,
        name: str,
        entity_type: str,
        search_params: Dict,
        description: Optional[str] = None,
        is_default: bool = False,
        is_public: bool = False,
    ) -> SavedSearch:
        try:
            if is_default:
                self.db.query(SavedSearch).filter(
                    SavedSearch.user_id == user_id,
                    SavedSearch.entity_type == entity_type,
                ).update({"is_default": False})

            obj = SavedSearch(
                user_id=user_id,
                name=name,
                entity_type=entity_type,
                search_params=search_params,
                description=description,
                is_default=is_default,
                is_public=is_public,
            )

            self.db.add(obj)
            self.db.commit()
            self.db.refresh(obj)
            return obj

        except Exception:
            self.db.rollback()
            raise

    # =========================
    # SEARCH HISTORY
    # =========================
    def track_search(
        self,
        user_id: int,
        entity_type: str,
        search_term: str,
        filters: Optional[Dict] = None,
        result_count: Optional[int] = None,
    ) -> SearchHistory:
        obj = SearchHistory(
            user_id=user_id,
            entity_type=entity_type,
            search_term=search_term,
            filters=filters,
            result_count=result_count,
        )

        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)

        return obj

    def get_search_suggestions(
        self, user_id: int, entity_type: str, partial_query: str, limit: int = 5
    ) -> List[str]:
        if not partial_query or len(partial_query) < 2:
            return []

        pattern = f"%{partial_query}%"

        rows = (
            self.db.query(SearchHistory.search_term)
            .filter(
                SearchHistory.user_id == user_id,
                SearchHistory.entity_type == entity_type,
                SearchHistory.search_term.ilike(pattern),
            )
            .group_by(SearchHistory.search_term)
            .order_by(func.count(SearchHistory.id).desc())
            .limit(limit)
            .all()
        )

        return [r[0] for r in rows]

    # =========================
    # QUICK FILTERS
    # =========================
    def get_quick_filters(
        self, entity_type: Optional[str] = None, user_role: Optional[str] = None
    ) -> List[QuickFilter]:
        q = self.db.query(QuickFilter).filter(QuickFilter.is_active.is_(True))

        if entity_type:
            q = q.filter(QuickFilter.entity_type == entity_type)

        if user_role:
            q = q.filter(
                or_(
                    QuickFilter.required_role.is_(None),
                    QuickFilter.required_role == user_role,
                )
            )

        return q.order_by(QuickFilter.display_order, QuickFilter.name).all()

    def get_saved_searches(
        self, user_id: int, entity_type: Optional[str] = None
    ) -> List[SavedSearch]:
        q = self.db.query(SavedSearch).filter(SavedSearch.user_id == user_id)

        if entity_type:
            q = q.filter(SavedSearch.entity_type == entity_type)

        return q.order_by(SavedSearch.created_at.desc()).all()

    def use_saved_search(self, search_id: int, user_id: int) -> Optional[SavedSearch]:
        obj = (
            self.db.query(SavedSearch)
            .filter(SavedSearch.id == search_id, SavedSearch.user_id == user_id)
            .first()
        )

        if not obj:
            return None

        obj.use_count = (obj.use_count or 0) + 1
        obj.last_used = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete_saved_search(self, search_id: int, user_id: int) -> bool:
        obj = (
            self.db.query(SavedSearch)
            .filter(SavedSearch.id == search_id, SavedSearch.user_id == user_id)
            .first()
        )

        if not obj:
            return False

        self.db.delete(obj)
        self.db.commit()
        return True

    def get_search_history(
        self, user_id: int, entity_type: Optional[str] = None, limit: int = 20
    ) -> List[SearchHistory]:
        q = self.db.query(SearchHistory).filter(SearchHistory.user_id == user_id)

        if entity_type:
            q = q.filter(SearchHistory.entity_type == entity_type)

        return q.order_by(SearchHistory.created_at.desc()).limit(limit).all()

    def create_quick_filter(
        self,
        name: str,
        entity_type: str,
        filter_config: Dict,
        icon: Optional[str] = None,
        color: Optional[str] = None,
        display_order: int = 0,
        required_role: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> QuickFilter:
        try:
            obj = QuickFilter(
                name=name,
                entity_type=entity_type,
                filter_config=filter_config,
                icon=icon,
                color=color,
                display_order=display_order,
                required_role=required_role,
                created_by=created_by,
                is_active=True,
            )

            self.db.add(obj)
            self.db.commit()
            self.db.refresh(obj)
            return obj

        except Exception:
            self.db.rollback()
            raise

    # =========================
    # SEARCH ANALYTICS
    # =========================
    def _window_filter(self, since_days: int):
        return datetime.now(timezone.utc) - timedelta(days=since_days)

    def top_queries(
        self,
        since_days: int = 30,
        limit: int = 20,
        entity_type: Optional[str] = None,
    ) -> List[Dict]:
        cutoff = self._window_filter(since_days)
        q = (
            self.db.query(
                SearchHistory.search_term,
                SearchHistory.entity_type,
                func.count(SearchHistory.id).label("hits"),
                func.avg(SearchHistory.result_count).label("avg_results"),
            )
            .filter(SearchHistory.created_at >= cutoff)
            .filter(SearchHistory.search_term != "")
        )
        if entity_type:
            q = q.filter(SearchHistory.entity_type == entity_type)
        rows = (
            q.group_by(SearchHistory.search_term, SearchHistory.entity_type)
            .order_by(desc("hits"))
            .limit(limit)
            .all()
        )
        return [
            {
                "search_term": r.search_term,
                "entity_type": r.entity_type,
                "hits": int(r.hits),
                "avg_results": float(r.avg_results) if r.avg_results is not None else 0.0,
            }
            for r in rows
        ]

    def zero_result_queries(
        self, since_days: int = 30, limit: int = 50, min_hits: int = 2
    ) -> List[Dict]:
        cutoff = self._window_filter(since_days)
        rows = (
            self.db.query(
                SearchHistory.search_term,
                SearchHistory.entity_type,
                func.count(SearchHistory.id).label("hits"),
                func.max(SearchHistory.created_at).label("last_seen"),
            )
            .filter(SearchHistory.created_at >= cutoff)
            .filter(SearchHistory.search_term != "")
            .filter(
                or_(
                    SearchHistory.result_count == 0,
                    SearchHistory.result_count.is_(None),
                )
            )
            .group_by(SearchHistory.search_term, SearchHistory.entity_type)
            .having(func.count(SearchHistory.id) >= min_hits)
            .order_by(desc("hits"))
            .limit(limit)
            .all()
        )
        return [
            {
                "search_term": r.search_term,
                "entity_type": r.entity_type,
                "hits": int(r.hits),
                "last_seen": r.last_seen.isoformat() if r.last_seen else None,
            }
            for r in rows
        ]

    def search_volume_by_hour(self, since_days: int = 7) -> List[Dict]:
        cutoff = self._window_filter(since_days)
        rows = (
            self.db.query(
                func.extract("hour", SearchHistory.created_at).label("hour"),
                func.count(SearchHistory.id).label("hits"),
            )
            .filter(SearchHistory.created_at >= cutoff)
            .group_by("hour")
            .order_by("hour")
            .all()
        )
        return [{"hour": int(r.hour or 0), "hits": int(r.hits)} for r in rows]

    def user_search_patterns(
        self, since_days: int = 30, limit: int = 20
    ) -> List[Dict]:
        cutoff = self._window_filter(since_days)
        rows = (
            self.db.query(
                SearchHistory.user_id,
                func.count(SearchHistory.id).label("total"),
            )
            .filter(SearchHistory.created_at >= cutoff)
            .group_by(SearchHistory.user_id)
            .order_by(desc("total"))
            .limit(limit)
            .all()
        )
        out: List[Dict] = []
        for r in rows:
            zero = (
                self.db.query(func.count(SearchHistory.id))
                .filter(SearchHistory.user_id == r.user_id)
                .filter(SearchHistory.created_at >= cutoff)
                .filter(
                    or_(
                        SearchHistory.result_count == 0,
                        SearchHistory.result_count.is_(None),
                    )
                )
                .scalar()
                or 0
            )
            user_row = (
                self.db.query(User.username)
                .filter(User.id == r.user_id)
                .first()
            )
            top_entity = (
                self.db.query(
                    SearchHistory.entity_type,
                    func.count(SearchHistory.id).label("c"),
                )
                .filter(SearchHistory.user_id == r.user_id)
                .filter(SearchHistory.created_at >= cutoff)
                .group_by(SearchHistory.entity_type)
                .order_by(desc("c"))
                .first()
            )
            total = int(r.total)
            out.append(
                {
                    "user_id": r.user_id,
                    "username": user_row[0] if user_row else None,
                    "total_searches": total,
                    "zero_result_searches": int(zero),
                    "zero_result_rate": (zero / total) if total else 0.0,
                    "top_entity": top_entity[0] if top_entity else None,
                }
            )
        return out

    def saved_filter_usage(
        self, since_days: int = 30, limit: int = 10
    ) -> List[Dict]:
        cutoff = self._window_filter(since_days)
        rows = (
            self.db.query(SavedSearch)
            .filter(
                or_(
                    SavedSearch.last_used.is_(None),
                    SavedSearch.last_used >= cutoff,
                )
            )
            .order_by(desc(SavedSearch.use_count))
            .limit(limit)
            .all()
        )
        return [
            {
                "id": s.id,
                "name": s.name,
                "entity_type": s.entity_type,
                "use_count": s.use_count or 0,
                "last_used": s.last_used.isoformat() if s.last_used else None,
                "is_public": bool(s.is_public),
            }
            for s in rows
        ]

    def analytics_summary(self, since_days: int = 30) -> Dict:
        cutoff = self._window_filter(since_days)
        base = self.db.query(SearchHistory).filter(
            SearchHistory.created_at >= cutoff
        )
        total = base.count()
        zero = base.filter(
            or_(
                SearchHistory.result_count == 0,
                SearchHistory.result_count.is_(None),
            )
        ).count()
        unique_users = (
            self.db.query(func.count(func.distinct(SearchHistory.user_id)))
            .filter(SearchHistory.created_at >= cutoff)
            .scalar()
            or 0
        )
        unique_terms = (
            self.db.query(func.count(func.distinct(SearchHistory.search_term)))
            .filter(SearchHistory.created_at >= cutoff)
            .scalar()
            or 0
        )
        return {
            "since_days": since_days,
            "total_searches": int(total),
            "zero_result_searches": int(zero),
            "zero_result_rate": (zero / total) if total else 0.0,
            "unique_users": int(unique_users),
            "unique_terms": int(unique_terms),
        }
