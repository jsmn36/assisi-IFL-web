from datetime import datetime
from typing import Dict
import pandas as pd
from sqlalchemy import create_engine, text
from app.analytics_database import get_pms_db_url, get_analytics_db_url


class DataExtractor:
    def __init__(self):
        self.pms_engine = create_engine(get_pms_db_url())
        self.analytics_engine = create_engine(get_analytics_db_url())

    def get_last_sync_timestamp(self, table_name: str) -> datetime:
        query = text(
            """
            SELECT last_sync_at
            FROM etl_sync_log
            WHERE table_name = :table_name
              AND status = 'success'
            ORDER BY created_at DESC
            LIMIT 1
        """
        )

        with self.analytics_engine.connect() as conn:
            result = conn.execute(query, {"table_name": table_name}).fetchone()

        if result:
            return result[0]
        return datetime(1970, 1, 1)

    def extract_reservations(self) -> pd.DataFrame:
        last_sync = self.get_last_sync_timestamp("reservations")
        query = """
            SELECT
                r.id as reservation_id,
                r.property_id,
                r.guest_id,
                r.room_type_id,
                r.check_in_date as start_date,
                r.check_out_date as end_date,
                r.status,
                r.source as channel,
                r.created_at,
                r.updated_at,
                (JULIANDAY(r.check_out_date) - JULIANDAY(r.check_in_date)) as nights,
                (JULIANDAY(r.check_in_date) - JULIANDAY(DATE(r.created_at))) as lead_time_days
            FROM reservations r
            WHERE r.updated_at > :last_sync
            ORDER BY r.updated_at ASC
        """
        # Note: Added SQLite JULIANDAY abstraction. In PostgreSQL this would be just `r.end_date - r.start_date`

        if self.pms_engine.dialect.name == "postgresql":
            query = """
                SELECT
                    r.id as reservation_id,
                    r.property_id,
                    r.guest_id,
                    r.room_type_id,
                    r.check_in_date as start_date,
                    r.check_out_date as end_date,
                    r.status,
                    r.source as channel,
                    r.created_at,
                    r.updated_at,
                    (r.check_out_date - r.check_in_date) as nights,
                    (r.check_in_date - r.created_at::date) as lead_time_days
                FROM reservations r
                WHERE r.updated_at > :last_sync
                ORDER BY r.updated_at ASC
            """

        with self.pms_engine.connect() as conn:
            result = conn.execute(text(query), {"last_sync": last_sync})
            df = pd.DataFrame(result.mappings().all())
        return df

    def extract_stays(self) -> pd.DataFrame:
        last_sync = self.get_last_sync_timestamp("stays")
        query = """
            SELECT
                s.id as stay_id,
                s.reservation_id,
                s.room_id,
                s.actual_check_in_time as check_in_time,
                s.actual_check_out_time as check_out_time,
                s.status,
                r.created_at,
                r.updated_at
            FROM stays s
            JOIN reservations r ON s.reservation_id = r.id
            WHERE r.updated_at > :last_sync
            ORDER BY r.updated_at ASC
        """
        with self.pms_engine.connect() as conn:
            result = conn.execute(text(query), {"last_sync": last_sync})
            df = pd.DataFrame(result.mappings().all())
        return df

    def extract_charges(self) -> pd.DataFrame:
        # Avoid column ambiguity/issues if needed
        last_sync = self.get_last_sync_timestamp("charges")

        # NOTE: PRD refers to `id` as string vs integer and `quantity`, let's just select all relevant
        query = """
            SELECT 
                c.id as charge_id, 
                c.stay_id, 
                c.amount,
                c.charge_type,
                c.description,
                c.post_date as posted_date,
                r.created_at, 
                r.updated_at
            FROM charges c
            JOIN stays s ON c.stay_id = s.id
            JOIN reservations r ON s.reservation_id = r.id
            WHERE r.updated_at > :last_sync
            ORDER BY r.updated_at ASC
        """
        try:
            with self.pms_engine.connect() as conn:
                result = conn.execute(text(query), {"last_sync": last_sync})
                df = pd.DataFrame(result.mappings().all())
        except Exception:
            # Fallback if table name is different
            query = "SELECT c.id as charge_id, c.stay_id, c.amount, c.charge_type, c.description, c.post_date as posted_date, r.created_at, r.updated_at FROM charge c JOIN stays s ON c.stay_id = s.id JOIN reservations r ON s.reservation_id = r.id WHERE r.updated_at > :last_sync ORDER BY r.updated_at ASC"
            with self.pms_engine.connect() as conn:
                result = conn.execute(text(query), {"last_sync": last_sync})
                df = pd.DataFrame(result.mappings().all())

        return df

    def get_properties(self) -> pd.DataFrame:
        with self.pms_engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT id as property_id, name as property_name, 100 as total_rooms FROM properties"
                )
            )
            return pd.DataFrame(result.mappings().all())

    def get_room_types(self) -> pd.DataFrame:
        with self.pms_engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT id as room_type_id, name as room_type_name FROM room_types"
                )
            )
            return pd.DataFrame(result.mappings().all())

    def get_guests(self) -> pd.DataFrame:
        try:
            with self.pms_engine.connect() as conn:
                result = conn.execute(
                    text(
                        "SELECT id as guest_id, country as guest_country, loyalty_tier as guest_loyalty_tier FROM guests"
                    )
                )
                return pd.DataFrame(result.mappings().all())
        except Exception:
            return pd.DataFrame(
                columns=["guest_id", "guest_country", "guest_loyalty_tier"]
            )

    def get_rooms(self) -> pd.DataFrame:
        with self.pms_engine.connect() as conn:
            result = conn.execute(text("SELECT id as room_id, room_number FROM rooms"))
            return pd.DataFrame(result.mappings().all())

    def extract_all(self) -> Dict[str, pd.DataFrame]:
        return {
            "reservations": self.extract_reservations(),
            "stays": self.extract_stays(),
            "charges": self.extract_charges(),
        }
