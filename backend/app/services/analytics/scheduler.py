import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.tenant_loop import run_for_each_tenant
from app.services.analytics.etl import run_etl_job

logger = logging.getLogger(__name__)

# Create a global scheduler instance
scheduler = BackgroundScheduler()


def run_etl_job_all_tenants():
    """Run analytics ETL once per active tenant."""
    return run_for_each_tenant(run_etl_job, job_name="analytics_etl")


def start_scheduler():
    """
    Start scheduled ETL jobs.
    Runs as a long-running background process inside the FastAPI app.
    """
    if scheduler.running:
        logger.warning("Scheduler is already running.")
        return

    logger.info("Initializing APScheduler for Analytics ETL pipeline...")

    # Schedule ETL every 5 minutes — per-tenant via the tenant-loop runner
    scheduler.add_job(
        func=run_etl_job_all_tenants,
        trigger=IntervalTrigger(minutes=5),
        id="etl_sync",
        replace_existing=True,
        max_instances=1,  # Prevent overlapping runs
        coalesce=True,  # Skip missed runs if previous run still going
    )

    # Note: As per PRD we could add daily metrics finalization at 3 AM here
    # but the 5 minute incremental logic in our `transform_daily_metrics` already covers it for Phase 1.

    scheduler.start()
    logger.info("APScheduler started successfully.")


def shutdown_scheduler():
    """Shutdown the scheduler gracefully."""
    if scheduler.running:
        logger.info("Shutting down APScheduler...")
        scheduler.shutdown(wait=False)
