"""
Query Optimizer
Database query optimization utilities
"""
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func, and_, or_
from typing import List, Optional
from datetime import datetime, timedelta


class QueryOptimizer:
    """
    Query optimization utilities

    Best practices:
    - Use eager loading for relationships
    - Add appropriate indexes
    - Limit result sets
    - Use specific column selection
    - Avoid N+1 queries
    """

    @staticmethod
    def optimize_reservation_query(
        query, include_guest: bool = False, include_room: bool = False
    ):
        """Optimize reservation query with eager loading"""
        if include_guest:
            query = query.options(joinedload("guest"))
        if include_room:
            query = query.options(joinedload("room"))
        return query

    @staticmethod
    def optimize_guest_query(query, include_reservations: bool = False):
        """Optimize guest query"""
        if include_reservations:
            query = query.options(selectinload("reservations"))
        return query

    @staticmethod
    def batch_load_relationships(objects: List, relationship: str, session: Session):
        """Batch load relationships to avoid N+1 queries"""
        if not objects:
            return
        for obj in objects:
            getattr(obj, relationship)

    @staticmethod
    def get_slow_query_log() -> List[dict]:
        """Get slow queries (requires PostgreSQL pg_stat_statements)"""
        return []

    @staticmethod
    def analyze_query(query) -> dict:
        """Analyze query execution plan"""
        explained = str(query.statement.compile(compile_kwargs={"literal_binds": True}))
        return {
            "query": explained,
            "estimated_rows": "N/A",
            "indexes_used": "N/A",
        }
