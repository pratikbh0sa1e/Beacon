"""
Scheduler for automated daily syncs
"""
import schedule
import time
import threading
import logging
from datetime import datetime

from backend.database import SessionLocal
from Agent.data_ingestion.sync_service import SyncService

logger = logging.getLogger(__name__)


class SyncScheduler:
    """Background scheduler for automated syncs"""
    
    def __init__(self):
        self.sync_service = SyncService()
        self.running = False
        self.thread = None
    
    def run_daily_sync(self):
        """Execute daily sync for all enabled sources"""
        logger.info(f"Starting scheduled sync at {datetime.now()}")
        
        db = SessionLocal()
        try:
            result = self.sync_service.sync_all_sources(db)
            logger.info(f"Scheduled sync complete: {result}")
        except Exception as e:
            logger.error(f"Scheduled sync failed: {str(e)}")
        finally:
            db.close()
    
    def start(self, sync_time: str = "02:00"):
        """
        Start the scheduler
        
        Args:
            sync_time: Time to run daily sync (HH:MM format, 24-hour)
        """
        if self.running:
            logger.warning("Scheduler already running")
            return
        
        # Schedule daily sync
        schedule.every().day.at(sync_time).do(self.run_daily_sync)
        
        logger.info(f"Scheduler started. Daily sync at {sync_time}")
        
        self.running = True
        
        # Run scheduler in background thread
        def run_scheduler():
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        self.thread = threading.Thread(target=run_scheduler, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        schedule.clear()
        logger.info("Scheduler stopped")
    
    def trigger_immediate_sync(self):
        """Trigger an immediate sync (outside schedule)"""
        logger.info("Triggering immediate sync")
        self.run_daily_sync()


# Global scheduler instance
_scheduler = None


def get_scheduler() -> SyncScheduler:
    """Get or create global scheduler instance"""
    global _scheduler
    if _scheduler is None:
        _scheduler = SyncScheduler()
    return _scheduler


def start_scheduler(sync_time: str = "02:00"):
    """Start the global scheduler"""
    scheduler = get_scheduler()
    scheduler.start(sync_time)


def stop_scheduler():
    """Stop the global scheduler"""
    scheduler = get_scheduler()
    scheduler.stop()
