import pandas as pd
from typing import Dict
from datetime import date


class DataTransformer:
    """
    Transforms raw PMS data into analytics-ready formats.

    Key Operations:
    - Denormalization (JOINs)
    - Aggregations
    - Calculated fields
    - Data quality validation
    """

    def transform_reservations(
        self,
        reservations_df: pd.DataFrame,
        properties_df: pd.DataFrame,
        room_types_df: pd.DataFrame,
        guests_df: pd.DataFrame,
    ) -> pd.DataFrame:
        if reservations_df.empty:
            return pd.DataFrame()

        df = reservations_df.merge(
            properties_df[["property_id", "property_name"]],
            on="property_id",
            how="left",
        )
        df = df.merge(
            room_types_df[["room_type_id", "room_type_name"]],
            on="room_type_id",
            how="left",
        )

        if not guests_df.empty:
            df = df.merge(
                guests_df[["guest_id", "guest_country", "guest_loyalty_tier"]],
                on="guest_id",
                how="left",
            )
        else:
            df["guest_country"] = None
            df["guest_loyalty_tier"] = None

        df["room_revenue"] = (
            df["nights"] * 0
        )  # Placeholder, needs real charges mapped later if possible
        df["total_revenue"] = df["room_revenue"]

        df["booking_date"] = pd.to_datetime(df["created_at"]).dt.date
        df["check_in_date"] = pd.to_datetime(df["start_date"]).dt.date
        df["check_out_date"] = pd.to_datetime(df["end_date"]).dt.date
        df["guests_count"] = 1  # default

        # Clean nulls
        df["guest_country"] = df["guest_country"].fillna("Unknown")
        df["guest_loyalty_tier"] = df["guest_loyalty_tier"].fillna("Unknown")

        # Validate schema
        df = df[df["reservation_id"].notna()]
        df = df[df["property_id"].notna()]
        df = df[df["check_in_date"].notna()]
        return df

    def transform_stays(
        self,
        stays_df: pd.DataFrame,
        reservations_df: pd.DataFrame,
        rooms_df: pd.DataFrame,
        charges_df: pd.DataFrame,
    ) -> pd.DataFrame:
        if stays_df.empty:
            return pd.DataFrame()

        df = stays_df.merge(
            reservations_df[
                [
                    "reservation_id",
                    "property_id",
                    "guest_id",
                    "room_type_id",
                    "room_type_name",
                ]
            ],
            on="reservation_id",
            how="left",
        )
        df = df.merge(rooms_df[["room_id", "room_number"]], on="room_id", how="left")

        if not charges_df.empty and "stay_id" in charges_df.columns:
            revenue_by_type = (
                charges_df.groupby(["stay_id", "charge_type"])["amount"]
                .sum()
                .unstack(fill_value=0)
            )
            df = df.merge(
                revenue_by_type, left_on="stay_id", right_index=True, how="left"
            )
        else:
            df["room"] = 0.0
            df["food"] = 0.0
            df["beverage"] = 0.0
            df["spa"] = 0.0
            df["other"] = 0.0

        for col in ["room", "food", "beverage", "spa", "other"]:
            if col not in df.columns:
                df[col] = 0.0

        df["room_revenue"] = df["room"].fillna(0)
        df["food_revenue"] = df["food"].fillna(0)
        df["beverage_revenue"] = df["beverage"].fillna(0)
        df["spa_revenue"] = df["spa"].fillna(0)
        df["other_revenue"] = df["other"].fillna(0)
        df["total_revenue"] = df[
            [
                "room_revenue",
                "food_revenue",
                "beverage_revenue",
                "spa_revenue",
                "other_revenue",
            ]
        ].sum(axis=1)

        df["check_in_date"] = pd.to_datetime(df["check_in_time"]).dt.date
        df["check_out_date"] = pd.to_datetime(
            df["check_out_time"].fillna(pd.Timestamp.now())
        ).dt.date
        df["nights_actual"] = (
            pd.to_datetime(df["check_out_date"]) - pd.to_datetime(df["check_in_date"])
        ).dt.days

        return df

    def transform_charges(
        self, charges_df: pd.DataFrame, reservations_df: pd.DataFrame
    ) -> pd.DataFrame:
        if charges_df.empty:
            return pd.DataFrame()
        df = charges_df.merge(
            reservations_df[["reservation_id", "property_id"]],
            left_on="stay_id",
            right_on="reservation_id",
            how="left",
        )
        df["property_id"] = df["property_id"].fillna(1).astype(int)
        df["department"] = "general"
        df["quantity"] = 1
        df["unit_price"] = df["amount"]

        # Default posted_date to created_at date when NULL
        if "posted_date" in df.columns:
            mask = df["posted_date"].isna()
            if mask.any() and "created_at" in df.columns:
                df.loc[mask, "posted_date"] = pd.to_datetime(
                    df.loc[mask, "created_at"]
                ).dt.date

        # Lowercase charge_type enum values for analytics consistency
        if "charge_type" in df.columns:
            df["charge_type"] = df["charge_type"].astype(str).str.lower()

        return df

    def calculate_daily_metrics(
        self,
        date_obj: pd.Timestamp,
        property_id: int,
        stays_df: pd.DataFrame,
        reservations_df: pd.DataFrame,
        charges_df: pd.DataFrame,
        total_rooms: int,
    ) -> Dict:
        target_date = date_obj.date()

        if not stays_df.empty:
            date_stays = stays_df[
                (stays_df["property_id"] == property_id)
                & (pd.to_datetime(stays_df["check_in_date"]).dt.date <= target_date)
                & (pd.to_datetime(stays_df["check_out_date"]).dt.date > target_date)
            ]
            rooms_occupied = len(date_stays)
            check_ins = len(
                stays_df[
                    pd.to_datetime(stays_df["check_in_date"]).dt.date == target_date
                ]
            )
            check_outs = len(
                stays_df[
                    pd.to_datetime(stays_df["check_out_date"]).dt.date == target_date
                ]
            )
        else:
            rooms_occupied = check_ins = check_outs = 0

        occupancy_percent = (
            (rooms_occupied / total_rooms) * 100 if total_rooms > 0 else 0
        )

        if not charges_df.empty:
            if "property_id" not in charges_df.columns:
                charges_df["property_id"] = property_id
            date_charges = charges_df[
                (charges_df["property_id"] == property_id)
                & (pd.to_datetime(charges_df["posted_date"]).dt.date == target_date)
            ]

            room_revenue = date_charges[date_charges["charge_type"] == "room"][
                "amount"
            ].sum()
            food_revenue = date_charges[date_charges["charge_type"] == "food"][
                "amount"
            ].sum()
            beverage_revenue = date_charges[date_charges["charge_type"] == "beverage"][
                "amount"
            ].sum()
            spa_revenue = date_charges[date_charges["charge_type"] == "spa"][
                "amount"
            ].sum()
            other_revenue = date_charges[
                ~date_charges["charge_type"].isin(["room", "food", "beverage", "spa"])
            ]["amount"].sum()
            total_revenue = date_charges["amount"].sum()
        else:
            room_revenue = (
                food_revenue
            ) = beverage_revenue = spa_revenue = other_revenue = total_revenue = 0

        adr = room_revenue / rooms_occupied if rooms_occupied > 0 else 0
        revpar = room_revenue / total_rooms if total_rooms > 0 else 0

        if not reservations_df.empty:
            date_reservations = reservations_df[
                (reservations_df["property_id"] == property_id)
                & (
                    pd.to_datetime(reservations_df["booking_date"]).dt.date
                    == target_date
                )
            ]
            reservations_created = len(date_reservations)

            date_cancellations = reservations_df[
                (reservations_df["property_id"] == property_id)
                & (reservations_df["status"].str.lower() == "cancelled")
                & (pd.to_datetime(reservations_df["updated_at"]).dt.date == target_date)
            ]
            reservations_cancelled = len(date_cancellations)
        else:
            reservations_created = reservations_cancelled = 0

        return {
            "metric_date": target_date,
            "property_id": int(property_id),
            "total_rooms": int(total_rooms),
            "rooms_occupied": int(rooms_occupied),
            "rooms_available": int(total_rooms) - int(rooms_occupied),
            "occupancy_percent": float(round(occupancy_percent, 2)),
            "room_revenue": float(room_revenue or 0),
            "food_revenue": float(food_revenue or 0),
            "beverage_revenue": float(beverage_revenue or 0),
            "spa_revenue": float(spa_revenue or 0),
            "other_revenue": float(other_revenue or 0),
            "total_revenue": float(total_revenue or 0),
            "adr": float(round(adr, 2)),
            "revpar": float(round(revpar, 2)),
            "reservations_created": int(reservations_created),
            "reservations_cancelled": int(reservations_cancelled),
            "check_ins": int(check_ins),
            "check_outs": int(check_outs),
        }
