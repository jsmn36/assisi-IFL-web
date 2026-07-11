from typing import Dict, Any, List
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
import math

from app.analytics_database import get_analytics_db_url
from app.models.analytics import (
    FactReservations,
    FactStays,
    FactCharges,
    AnalyticsDailyMetrics,
)


class DataLoader:
    """
    Loads transformed data into analytics database.

    Key Features:
    - Upsert operations (INSERT ... ON CONFLICT UPDATE)
    - Transaction atomicity
    - Idempotency (safe to re-run)
    """

    def __init__(self):
        self.engine = create_engine(get_analytics_db_url())

    def _clean_records(self, df: pd.DataFrame) -> List[Dict]:
        """Convert df to records and clean NaNs to None for DB compatibility"""
        records = df.to_dict("records")
        for record in records:
            for k, v in record.items():
                if isinstance(v, float) and math.isnan(v):
                    record[k] = None
                elif pd.isna(v):
                    record[k] = None
        return records

    def _filter_columns(self, df: pd.DataFrame, model_class) -> pd.DataFrame:
        """Filter DataFrame to only include columns that exist in the target model,
        and convert datetime/date columns to proper Python types for SQLite compatibility.
        """
        from sqlalchemy import DateTime, Date

        valid_columns = {c.key: c for c in model_class.__table__.columns}
        existing = [c for c in df.columns if c in valid_columns]
        df = df[existing].copy()

        # Convert datetime/date string columns to proper Python types
        for col_name in existing:
            col_type = valid_columns[col_name].type
            if isinstance(col_type, DateTime):
                df[col_name] = pd.to_datetime(df[col_name], errors="coerce")
                # Convert from pandas Timestamp to Python datetime
                df[col_name] = df[col_name].apply(
                    lambda x: x.to_pydatetime() if pd.notna(x) else None
                )
            elif isinstance(col_type, Date):
                df[col_name] = pd.to_datetime(df[col_name], errors="coerce")
                df[col_name] = df[col_name].apply(
                    lambda x: x.date() if pd.notna(x) else None
                )

        return df

    def upsert_fact_reservations(self, df: pd.DataFrame) -> int:
        if df.empty:
            return 0
        df = self._filter_columns(df, FactReservations)
        records = self._clean_records(df)
        dialect = self.engine.dialect.name

        with self.engine.begin() as conn:
            if dialect == "postgresql":
                stmt = pg_insert(FactReservations).values(records)
                stmt = stmt.on_conflict_do_update(
                    index_elements=["reservation_id"], set_=dict(stmt.excluded)
                )
                result = conn.execute(stmt)
                return result.rowcount
            elif dialect == "sqlite":
                from sqlalchemy.dialects.sqlite import insert as sqlite_insert

                stmt = sqlite_insert(FactReservations).values(records)
                stmt = stmt.on_conflict_do_update(
                    index_elements=["reservation_id"],
                    set_={
                        k: getattr(stmt.excluded, k)
                        for k in records[0].keys()
                        if k != "reservation_id"
                    },
                )
                result = conn.execute(stmt)
                return result.rowcount
            else:
                conn.execute(
                    FactReservations.__table__.insert().prefix_with("OR REPLACE"),
                    records,
                )
                return len(records)

    def upsert_fact_stays(self, df: pd.DataFrame) -> int:
        if df.empty:
            return 0
        df = self._filter_columns(df, FactStays)
        records = self._clean_records(df)
        dialect = self.engine.dialect.name

        with self.engine.begin() as conn:
            if dialect == "postgresql":
                stmt = pg_insert(FactStays).values(records)
                stmt = stmt.on_conflict_do_update(
                    index_elements=["stay_id"], set_=dict(stmt.excluded)
                )
                result = conn.execute(stmt)
                return result.rowcount
            elif dialect == "sqlite":
                from sqlalchemy.dialects.sqlite import insert as sqlite_insert

                stmt = sqlite_insert(FactStays).values(records)
                stmt = stmt.on_conflict_do_update(
                    index_elements=["stay_id"],
                    set_={
                        k: getattr(stmt.excluded, k)
                        for k in records[0].keys()
                        if k != "stay_id"
                    },
                )
                result = conn.execute(stmt)
                return result.rowcount
            else:
                conn.execute(
                    FactStays.__table__.insert().prefix_with("OR REPLACE"), records
                )
                return len(records)

    def upsert_fact_charges(self, df: pd.DataFrame) -> int:
        if df.empty:
            return 0
        df = self._filter_columns(df, FactCharges)
        records = self._clean_records(df)
        dialect = self.engine.dialect.name

        with self.engine.begin() as conn:
            if dialect == "postgresql":
                stmt = pg_insert(FactCharges).values(records)
                stmt = stmt.on_conflict_do_nothing(index_elements=["charge_id"])
                result = conn.execute(stmt)
                return result.rowcount
            elif dialect == "sqlite":
                from sqlalchemy.dialects.sqlite import insert as sqlite_insert

                stmt = sqlite_insert(FactCharges).values(records)
                stmt = stmt.on_conflict_do_nothing(index_elements=["charge_id"])
                result = conn.execute(stmt)
                return result.rowcount
            else:
                return 0

    def upsert_daily_metrics(self, metrics: Dict[str, Any]) -> int:
        dialect = self.engine.dialect.name
        with self.engine.begin() as conn:
            if dialect == "postgresql":
                stmt = pg_insert(AnalyticsDailyMetrics).values([metrics])
                stmt = stmt.on_conflict_do_update(
                    index_elements=["metric_date", "property_id"],
                    set_=dict(stmt.excluded),
                )
                result = conn.execute(stmt)
                return result.rowcount
            elif dialect == "sqlite":
                from sqlalchemy.dialects.sqlite import insert as sqlite_insert

                stmt = sqlite_insert(AnalyticsDailyMetrics).values([metrics])
                metrics_copy = {
                    k: v
                    for k, v in metrics.items()
                    if k not in ["metric_date", "property_id"]
                }

                stmt = stmt.on_conflict_do_update(
                    index_elements=["metric_date", "property_id"], set_=metrics_copy
                )
                result = conn.execute(stmt)
                return result.rowcount
            return 0

    def log_sync_completion(
        self,
        table_name: str,
        records_extracted: int,
        records_transformed: int,
        records_loaded: int,
        duration_seconds: float,
        status: str,
        error_message: str = None,
    ):
        with self.engine.begin() as conn:
            query = text(
                """
                INSERT INTO etl_sync_log (
                    table_name, last_sync_at, records_extracted, records_transformed,
                    records_loaded, duration_seconds, status, error_message, created_at
                ) VALUES (
                    :table_name, CURRENT_TIMESTAMP, :records_extracted, :records_transformed,
                    :records_loaded, :duration_seconds, :status, :error_message, CURRENT_TIMESTAMP
                )
            """
            )
            conn.execute(
                query,
                {
                    "table_name": table_name,
                    "records_extracted": records_extracted,
                    "records_transformed": records_transformed,
                    "records_loaded": records_loaded,
                    "duration_seconds": duration_seconds,
                    "status": status,
                    "error_message": error_message,
                },
            )
