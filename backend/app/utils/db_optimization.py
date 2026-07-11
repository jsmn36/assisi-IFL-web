from sqlalchemy import event
from sqlalchemy.engine import Engine
import logging
from typing import Dict

# ✅ FIX: __name__ instead of name
logger = logging.getLogger(__name__)


def setup_connection_pool_logging(engine: Engine) -> None:
    """
    Setup connection pool event logging

    Logs pool checkouts and checkins for monitoring
    """

    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        logger.debug("Database connection established")

    @event.listens_for(engine, "checkout")
    def receive_checkout(dbapi_conn, connection_record, connection_proxy):
        logger.debug("Connection checked out from pool")

    @event.listens_for(engine, "checkin")
    def receive_checkin(dbapi_conn, connection_record):
        logger.debug("Connection returned to pool")


def get_pool_status(engine: Engine) -> Dict[str, int]:
    """
    Get current connection pool status

    Returns:
        Dictionary with pool statistics
    """
    pool = engine.pool

    return {
        "size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "total_connections": pool.size() + pool.overflow(),
    }


def optimize_query_for_large_dataset(query, batch_size: int = 1000):
    """
    Optimize query for large dataset processing

    Uses yield_per for efficient memory usage
    """
    return query.yield_per(batch_size).enable_eagerloads(False)
