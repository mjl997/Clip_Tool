from apscheduler.schedulers.background import BackgroundScheduler
from .services.storage import storage
from .services.db import db_service
import datetime
import logging

logger = logging.getLogger(__name__)

def cleanup_jobs():
    logger.info("Running cleanup job...")
    # Get jobs older than 24h
    # In a real scenario, we would query DB for old jobs
    # For now, let's just list MinIO top level folders?
    # Or rely on DB created_at.
    
    # We don't have a method to get old jobs in DBService yet, but we can add it or just iterate recent ones.
    # Let's add a method to DBService for fetching expired jobs.
    pass

scheduler = BackgroundScheduler()
# scheduler.add_job(cleanup_jobs, 'interval', hours=1)
