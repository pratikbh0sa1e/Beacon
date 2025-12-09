"""
Scraping Scheduler for executing scraping jobs at configured times
"""
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime, time as dt_time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
import pytz

logger = logging.getLogger(__name__)


class ScrapingScheduler:
    """Manages scheduled scraping jobs using APScheduler"""
    
    def __init__(self, storage, web_source_manager, health_monitor):
        """
        Initialize scraping scheduler
        
        Args:
            storage: LocalStorage instance
            web_source_manager: WebSourceManager instance
            health_monitor: HealthMonitor instance
        """
        self.storage = storage
        self.web_source_manager = web_source_manager
        self.health_monitor = health_monitor
        self.scheduler = BackgroundScheduler(timezone=pytz.UTC)
        self.scheduled_jobs = {}  # source_id -> job_id mapping
        
        logger.info("ScrapingScheduler initialized")
    
    def start(self):
        """Start the scheduler background process"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("ScrapingScheduler started")
            
            # Load and schedule all enabled sources
            self._initialize_scheduled_sources()
        else:
            logger.warning("ScrapingScheduler already running")
    
    def shutdown(self, wait: bool = True):
        """
        Gracefully shutdown the scheduler
        
        Args:
            wait: Whether to wait for running jobs to complete
        """
        if self.scheduler.running:
            self.scheduler.shutdown(wait=wait)
            logger.info(f"ScrapingScheduler shutdown (wait={wait})")
        else:
            logger.warning("ScrapingScheduler not running")
    
    def _initialize_scheduled_sources(self):
        """Load all scheduled sources from storage and create jobs"""
        sources = self.storage.list_sources()
        scheduled_count = 0
        
        for source in sources:
            if source.get('schedule_enabled', False):
                try:
                    self._schedule_source_internal(source)
                    scheduled_count += 1
                except Exception as e:
                    logger.error(f"Failed to schedule source {source['id']}: {str(e)}")
        
        logger.info(f"Initialized {scheduled_count} scheduled sources")
    
    def schedule_source(self, source_id: int, schedule_config: Dict[str, Any]) -> str:
        """
        Schedule scraping for a source
        
        Args:
            source_id: Database ID of the source
            schedule_config: Dict with:
                - type: 'daily', 'weekly', 'interval', 'custom'
                - time: Time string (e.g., '02:00' for daily)
                - interval_minutes: For interval type
                - cron: Cron expression for custom
        
        Returns:
            job_id: Unique identifier for the scheduled job
        """
        source = self.storage.get_source(source_id)
        if not source:
            raise ValueError(f"Source {source_id} not found")
        
        # Update source with schedule config
        self.storage.update_source(source_id, {
            'schedule_type': schedule_config['type'],
            'schedule_time': schedule_config.get('time'),
            'schedule_enabled': True
        })
        
        # Reload source with updated config
        source = self.storage.get_source(source_id)
        
        # Schedule the job
        job_id = self._schedule_source_internal(source)
        
        logger.info(f"Scheduled source {source_id} with job_id {job_id}")
        
        return job_id
    
    def _schedule_source_internal(self, source: Dict[str, Any]) -> str:
        """
        Internal method to schedule a source
        
        Args:
            source: Source configuration
        
        Returns:
            job_id
        """
        source_id = source['id']
        schedule_type = source.get('schedule_type', 'daily')
        schedule_time = source.get('schedule_time', '02:00')
        
        # Remove existing job if any
        if source_id in self.scheduled_jobs:
            self.unschedule_source(source_id)
        
        # Create trigger based on schedule type
        trigger = self._create_trigger(schedule_type, schedule_time)
        
        # Add job to scheduler
        job = self.scheduler.add_job(
            func=self.execute_job,
            trigger=trigger,
            args=[source_id],
            id=f"source_{source_id}",
            name=f"Scrape {source.get('name', source_id)}",
            replace_existing=True
        )
        
        # Store job reference
        self.scheduled_jobs[source_id] = job.id
        
        # Update next run time in storage
        next_run = self.get_next_run_time(source_id)
        if next_run:
            self.storage.update_source(source_id, {
                'next_scheduled_run': next_run.isoformat()
            })
        
        logger.info(
            f"Scheduled source {source_id} ({schedule_type}) - "
            f"next run: {next_run}"
        )
        
        return job.id
    
    def _create_trigger(self, schedule_type: str, schedule_time: str):
        """
        Create APScheduler trigger based on schedule type
        
        Args:
            schedule_type: Type of schedule
            schedule_time: Time configuration
        
        Returns:
            APScheduler trigger
        """
        if schedule_type == 'daily':
            # Parse time (e.g., '02:00')
            hour, minute = map(int, schedule_time.split(':'))
            return CronTrigger(hour=hour, minute=minute)
        
        elif schedule_type == 'weekly':
            # Weekly on Monday at specified time
            hour, minute = map(int, schedule_time.split(':'))
            return CronTrigger(day_of_week='mon', hour=hour, minute=minute)
        
        elif schedule_type == 'interval':
            # Interval in minutes (schedule_time contains minutes)
            minutes = int(schedule_time)
            return IntervalTrigger(minutes=minutes)
        
        elif schedule_type == 'custom':
            # Custom cron expression
            return CronTrigger.from_crontab(schedule_time)
        
        else:
            # Default to daily at 2 AM
            return CronTrigger(hour=2, minute=0)
    
    def unschedule_source(self, source_id: int) -> bool:
        """
        Remove scheduled job for a source
        
        Args:
            source_id: Source ID
        
        Returns:
            True if job was removed
        """
        if source_id in self.scheduled_jobs:
            job_id = self.scheduled_jobs[source_id]
            
            try:
                self.scheduler.remove_job(job_id)
                del self.scheduled_jobs[source_id]
                
                # Update source
                self.storage.update_source(source_id, {
                    'schedule_enabled': False,
                    'next_scheduled_run': None
                })
                
                logger.info(f"Unscheduled source {source_id}")
                return True
            
            except Exception as e:
                logger.error(f"Error unscheduling source {source_id}: {str(e)}")
                return False
        
        return False
    
    def get_next_run_time(self, source_id: int) -> Optional[datetime]:
        """
        Get next scheduled run time for a source
        
        Args:
            source_id: Source ID
        
        Returns:
            Next run time or None
        """
        if source_id in self.scheduled_jobs:
            job_id = self.scheduled_jobs[source_id]
            job = self.scheduler.get_job(job_id)
            
            if job:
                # APScheduler 3.x uses next_run_time attribute
                return getattr(job, 'next_run_time', None)
        
        return None
    
    def execute_job(self, source_id: int) -> Dict[str, Any]:
        """
        Execute a scraping job (called by scheduler or manually)
        
        Args:
            source_id: Source ID to scrape
        
        Returns:
            Job execution result
        """
        logger.info(f"Executing scheduled job for source {source_id}")
        start_time = datetime.utcnow()
        
        # Get source configuration
        source = self.storage.get_source(source_id)
        if not source:
            logger.error(f"Source {source_id} not found")
            return {
                'status': 'error',
                'error': 'Source not found'
            }
        
        # Create job record
        job_data = {
            'source_id': source_id,
            'status': 'running',
            'triggered_by': 'scheduled',
            'started_at': start_time.isoformat()
        }
        job = self.storage.create_job(job_data)
        job_id = job['id']
        
        try:
            # Execute scraping with all features
            result = self.web_source_manager.scrape_source_with_pagination(
                source_id=source_id,
                url=source['url'],
                source_name=source['name'],
                keywords=source.get('keywords'),
                pagination_enabled=source.get('pagination_enabled', False),
                max_pages=source.get('max_pages', 10),
                incremental=True  # Always use incremental for scheduled jobs
            )
            
            end_time = datetime.utcnow()
            execution_time = int((end_time - start_time).total_seconds())
            
            # Update job with results
            self.storage.update_job(job_id, {
                'status': result['status'],
                'completed_at': end_time.isoformat(),
                'documents_discovered': result.get('documents_discovered', 0),
                'documents_matched': result.get('documents_matched', 0),
                'documents_new': result.get('documents_new', 0),
                'documents_skipped': result.get('documents_skipped', 0),
                'execution_time_seconds': execution_time,
                'error_message': result.get('error') if result['status'] == 'error' else None
            })
            
            # Update source last scraped time
            self.storage.update_source(source_id, {
                'last_scraped_at': end_time.isoformat(),
                'last_scrape_status': result['status'],
                'total_documents_scraped': source.get('total_documents_scraped', 0) + result.get('documents_new', 0)
            })
            
            # Record in health monitor
            success = result['status'] == 'success'
            self.health_monitor.record_job_execution(
                source_id=source_id,
                status=result['status'],
                documents_found=result.get('documents_new', 0),
                execution_time=execution_time,
                error=result.get('error')
            )
            
            # Update next run time
            next_run = self.get_next_run_time(source_id)
            if next_run:
                self.storage.update_source(source_id, {
                    'next_scheduled_run': next_run.isoformat()
                })
            
            logger.info(
                f"Job {job_id} completed: {result['status']} - "
                f"{result.get('documents_new', 0)} new documents in {execution_time}s"
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Error executing job for source {source_id}: {str(e)}", exc_info=True)
            
            end_time = datetime.utcnow()
            execution_time = int((end_time - start_time).total_seconds())
            
            # Update job with error
            self.storage.update_job(job_id, {
                'status': 'failed',
                'completed_at': end_time.isoformat(),
                'error_message': str(e),
                'execution_time_seconds': execution_time
            })
            
            # Record failure in health monitor
            self.health_monitor.record_job_execution(
                source_id=source_id,
                status='failed',
                documents_found=0,
                execution_time=execution_time,
                error=str(e)
            )
            
            return {
                'status': 'error',
                'source_id': source_id,
                'error': str(e)
            }
    
    def execute_job_manual(self, source_id: int) -> Dict[str, Any]:
        """
        Manually trigger a job execution
        
        Args:
            source_id: Source ID
        
        Returns:
            Job result
        """
        logger.info(f"Manual execution triggered for source {source_id}")
        
        # Similar to execute_job but with 'manual' trigger
        source = self.storage.get_source(source_id)
        if not source:
            return {'status': 'error', 'error': 'Source not found'}
        
        start_time = datetime.utcnow()
        
        job_data = {
            'source_id': source_id,
            'status': 'running',
            'triggered_by': 'manual',
            'started_at': start_time.isoformat()
        }
        job = self.storage.create_job(job_data)
        
        # Execute the job
        return self.execute_job(source_id)
    
    def get_scheduled_sources(self) -> list:
        """
        Get list of all scheduled sources
        
        Returns:
            List of sources with scheduling info
        """
        sources = self.storage.list_sources()
        scheduled = []
        
        for source in sources:
            if source.get('schedule_enabled', False):
                next_run = self.get_next_run_time(source['id'])
                source['next_run_time'] = next_run.isoformat() if next_run else None
                scheduled.append(source)
        
        return scheduled
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """
        Get scheduler status
        
        Returns:
            Status information
        """
        return {
            'running': self.scheduler.running,
            'scheduled_jobs': len(self.scheduled_jobs),
            'sources': list(self.scheduled_jobs.keys())
        }
    
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.shutdown(wait=True)
