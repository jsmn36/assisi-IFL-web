import time
import logging
import traceback
from datetime import datetime
import pandas as pd

from app.services.analytics.extract import DataExtractor
from app.services.analytics.transform import DataTransformer
from app.services.analytics.load import DataLoader
from app.analytics_database import get_analytics_db_url

logger = logging.getLogger(__name__)


class ETLOrchestrator:
    """
    Orchestrates the complete ETL pipeline.
    Runs every 5 minutes to sync latest data.
    """

    def __init__(self):
        self.extractor = DataExtractor()
        self.transformer = DataTransformer()
        self.loader = DataLoader()

    def run_etl_cycle(self):
        start_time = time.time()
        logger.info("Starting ETL cycle...")

        try:
            raw_data = self.extractor.extract_all()
            reservations_df = raw_data["reservations"]
            stays_df = raw_data["stays"]
            charges_df = raw_data["charges"]

            records_extracted = len(reservations_df) + len(stays_df) + len(charges_df)

            if records_extracted == 0:
                logger.info("No new records to extract. Skipping transform and load.")
                return

            properties_df = self.extractor.get_properties()
            room_types_df = self.extractor.get_room_types()
            guests_df = self.extractor.get_guests()
            rooms_df = self.extractor.get_rooms()

            # Enrich reservations_df with room_type_name for downstream transforms
            if (
                not reservations_df.empty
                and not room_types_df.empty
                and "room_type_id" in reservations_df.columns
                and "room_type_id" in room_types_df.columns
            ):
                reservations_df = reservations_df.merge(
                    room_types_df[["room_type_id", "room_type_name"]],
                    on="room_type_id",
                    how="left",
                )
            elif not reservations_df.empty:
                reservations_df["room_type_name"] = "Unknown"

            fact_reservations = self.transformer.transform_reservations(
                reservations_df, properties_df, room_types_df, guests_df
            )
            fact_stays = self.transformer.transform_stays(
                stays_df, reservations_df, rooms_df, charges_df
            )
            fact_charges = self.transformer.transform_charges(
                charges_df, reservations_df
            )

            records_transformed = (
                len(fact_reservations) + len(fact_stays) + len(fact_charges)
            )

            rows_loaded = 0
            rows_loaded += self.loader.upsert_fact_reservations(fact_reservations)
            rows_loaded += self.loader.upsert_fact_stays(fact_stays)
            rows_loaded += self.loader.upsert_fact_charges(fact_charges)

            today = pd.Timestamp.now()
            for property_id in properties_df["property_id"].unique():
                prop_data = properties_df[properties_df["property_id"] == property_id]
                if not prop_data.empty:
                    total_rooms = prop_data["total_rooms"].iloc[0]
                    metrics = self.transformer.calculate_daily_metrics(
                        date_obj=today,
                        property_id=property_id,
                        stays_df=fact_stays,
                        reservations_df=fact_reservations,
                        charges_df=fact_charges,
                        total_rooms=total_rooms,
                    )
                    self.loader.upsert_daily_metrics(metrics)

            duration = time.time() - start_time
            self.loader.log_sync_completion(
                table_name="all",
                records_extracted=records_extracted,
                records_transformed=records_transformed,
                records_loaded=rows_loaded,
                duration_seconds=round(duration, 2),
                status="success",
            )
            logger.info(f"ETL cycle completed successfully in {duration:.2f} seconds")

        except Exception as e:
            logger.error(f"ETL cycle failed: {str(e)}", exc_info=True)
            duration = time.time() - start_time
            error_msg = traceback.format_exc()[:1000]  # truncate
            try:
                self.loader.log_sync_completion(
                    table_name="all",
                    records_extracted=0,
                    records_transformed=0,
                    records_loaded=0,
                    duration_seconds=round(duration, 2),
                    status="failed",
                    error_message=error_msg,
                )
            except Exception as log_err:
                logger.error(f"Failed to write ETL error log: {str(log_err)}")
            # Do not re-raise in scheduler, just log


def run_etl_job():
    """Entry point for scheduled ETL job."""
    try:
        orchestrator = ETLOrchestrator()
        orchestrator.run_etl_cycle()
    except Exception as e:
        logger.error(f"ETL job execution failed: {e}")
