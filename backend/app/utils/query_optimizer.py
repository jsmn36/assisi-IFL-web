from sqlalchemy.orm import Query, joinedload, selectinload
from typing import List, Optional
from sqlalchemy import func


class QueryOptimizer:
    """
    Common query optimization patterns
    """

    @staticmethod
    def paginate(query: Query, page: int = 1, per_page: int = 50) -> Query:
        """
        Efficient pagination
        """
        if page < 1:
            page = 1
        if per_page < 1:
            per_page = 50

        offset = (page - 1) * per_page
        return query.offset(offset).limit(per_page)

    @staticmethod
    def eager_load_reservations(query: Query) -> Query:
        """
        Eager load reservation relationships
        NOTE: Use model attributes instead of strings
        """
        from app.models import Reservation  # adjust import as needed

        return query.options(
            joinedload(Reservation.guest),
            joinedload(Reservation.room),
            selectinload(Reservation.payments),
            selectinload(Reservation.charges),
        )

    @staticmethod
    def optimize_for_api(
        query: Query, relationships: Optional[List[str]] = None
    ) -> Query:
        """
        Optimize query for API response
        """
        if not relationships:
            return query

        options = []

        for rel in relationships:
            parts = rel.split(".")
            loader = joinedload(parts[0])

            # Handle nested relationships properly
            for sub_rel in parts[1:]:
                loader = loader.joinedload(sub_rel)

            options.append(loader)

        return query.options(*options)

    @staticmethod
    def count_query(query: Query) -> int:
        """
        Efficient count without loading objects
        Handles complex queries safely
        """
        count_q = query.order_by(None)  # remove ORDER BY for performance
        return count_q.count()
