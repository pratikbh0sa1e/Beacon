"""
Local file-based storage for web scraping data (temporary, no database)
This allows development and testing without database access
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import hashlib


class LocalStorage:
    """File-based storage for scraping data"""
    
    def __init__(self, storage_dir: str = "data/scraping_storage"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Storage files
        self.sources_file = self.storage_dir / "sources.json"
        self.jobs_file = self.storage_dir / "jobs.json"
        self.tracker_file = self.storage_dir / "document_tracker.json"
        self.health_file = self.storage_dir / "health_metrics.json"
        self.logs_file = self.storage_dir / "scraping_logs.json"
        
        # Initialize files if they don't exist
        self._initialize_files()
    
    def _initialize_files(self):
        """Create empty storage files if they don't exist"""
        for file in [self.sources_file, self.jobs_file, self.tracker_file, self.health_file, self.logs_file]:
            if not file.exists():
                self._write_json(file, {})
    
    def _read_json(self, file_path: Path) -> Dict:
        """Read JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _write_json(self, file_path: Path, data: Dict):
        """Write JSON file"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
    
    # ==================== SOURCES ====================
    
    def create_source(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new scraping source"""
        sources = self._read_json(self.sources_file)
        
        # Generate ID
        source_id = max([int(k) for k in sources.keys()], default=0) + 1
        
        # Add metadata
        source_data['id'] = source_id
        source_data['created_at'] = datetime.utcnow().isoformat()
        source_data['updated_at'] = datetime.utcnow().isoformat()
        
        # Set defaults
        source_data.setdefault('pagination_enabled', False)
        source_data.setdefault('max_pages', 10)
        source_data.setdefault('schedule_enabled', False)
        source_data.setdefault('schedule_type', None)
        source_data.setdefault('schedule_time', None)
        source_data.setdefault('next_scheduled_run', None)
        source_data.setdefault('total_documents_scraped', 0)
        source_data.setdefault('last_scraped_at', None)
        source_data.setdefault('last_scrape_status', None)
        
        sources[str(source_id)] = source_data
        self._write_json(self.sources_file, sources)
        
        return source_data
    
    def get_source(self, source_id: int) -> Optional[Dict[str, Any]]:
        """Get a source by ID"""
        sources = self._read_json(self.sources_file)
        return sources.get(str(source_id))
    
    def list_sources(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """List all sources"""
        sources = self._read_json(self.sources_file)
        source_list = list(sources.values())
        
        if enabled_only:
            source_list = [s for s in source_list if s.get('scraping_enabled', True)]
        
        return source_list
    
    def update_source(self, source_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a source"""
        sources = self._read_json(self.sources_file)
        
        if str(source_id) not in sources:
            return None
        
        sources[str(source_id)].update(updates)
        sources[str(source_id)]['updated_at'] = datetime.utcnow().isoformat()
        
        self._write_json(self.sources_file, sources)
        return sources[str(source_id)]
    
    def delete_source(self, source_id: int) -> bool:
        """Delete a source"""
        sources = self._read_json(self.sources_file)
        
        if str(source_id) in sources:
            del sources[str(source_id)]
            self._write_json(self.sources_file, sources)
            return True
        
        return False
    
    # ==================== JOBS ====================
    
    def create_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new scraping job"""
        jobs = self._read_json(self.jobs_file)
        
        # Generate ID
        job_id = max([int(k) for k in jobs.keys()], default=0) + 1
        
        # Add metadata
        job_data['id'] = job_id
        job_data['created_at'] = datetime.utcnow().isoformat()
        job_data.setdefault('status', 'pending')
        job_data.setdefault('documents_discovered', 0)
        job_data.setdefault('documents_matched', 0)
        job_data.setdefault('documents_new', 0)
        job_data.setdefault('documents_skipped', 0)
        job_data.setdefault('retry_count', 0)
        
        jobs[str(job_id)] = job_data
        self._write_json(self.jobs_file, jobs)
        
        return job_data
    
    def update_job(self, job_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a job"""
        jobs = self._read_json(self.jobs_file)
        
        if str(job_id) not in jobs:
            return None
        
        jobs[str(job_id)].update(updates)
        self._write_json(self.jobs_file, jobs)
        
        return jobs[str(job_id)]
    
    def get_jobs_by_source(self, source_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Get jobs for a specific source"""
        jobs = self._read_json(self.jobs_file)
        
        source_jobs = [
            job for job in jobs.values()
            if job.get('source_id') == source_id
        ]
        
        # Sort by created_at descending
        source_jobs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return source_jobs[:limit]
    
    # ==================== DOCUMENT TRACKER ====================
    
    def is_document_scraped(self, url: str) -> bool:
        """Check if a document URL has been scraped"""
        tracker = self._read_json(self.tracker_file)
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return url_hash in tracker
    
    def get_document_hash(self, url: str) -> Optional[str]:
        """Get the stored content hash for a URL"""
        tracker = self._read_json(self.tracker_file)
        url_hash = hashlib.md5(url.encode()).hexdigest()
        
        if url_hash in tracker:
            return tracker[url_hash].get('content_hash')
        
        return None
    
    def mark_document_scraped(self, url: str, content_hash: str, source_id: int):
        """Mark a document as scraped"""
        tracker = self._read_json(self.tracker_file)
        url_hash = hashlib.md5(url.encode()).hexdigest()
        
        now = datetime.utcnow().isoformat()
        
        if url_hash in tracker:
            # Update existing entry
            tracker[url_hash]['last_seen_at'] = now
            tracker[url_hash]['content_hash'] = content_hash
        else:
            # Create new entry
            tracker[url_hash] = {
                'document_url': url,
                'content_hash': content_hash,
                'source_id': source_id,
                'first_scraped_at': now,
                'last_seen_at': now
            }
        
        self._write_json(self.tracker_file, tracker)
    
    def get_tracked_documents_by_source(self, source_id: int) -> List[Dict[str, Any]]:
        """Get all tracked documents for a source"""
        tracker = self._read_json(self.tracker_file)
        
        return [
            doc for doc in tracker.values()
            if doc.get('source_id') == source_id
        ]
    
    # ==================== HEALTH METRICS ====================
    
    def get_health_metrics(self, source_id: int) -> Dict[str, Any]:
        """Get health metrics for a source"""
        health = self._read_json(self.health_file)
        
        if str(source_id) not in health:
            # Initialize metrics
            health[str(source_id)] = {
                'source_id': source_id,
                'total_executions': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'consecutive_failures': 0,
                'last_success_at': None,
                'last_failure_at': None,
                'average_execution_time': None,
                'total_documents_found': 0,
                'average_documents_per_run': None,
                'updated_at': datetime.utcnow().isoformat()
            }
            self._write_json(self.health_file, health)
        
        return health[str(source_id)]
    
    def update_health_metrics(self, source_id: int, updates: Dict[str, Any]):
        """Update health metrics for a source"""
        health = self._read_json(self.health_file)
        
        if str(source_id) not in health:
            self.get_health_metrics(source_id)  # Initialize
            health = self._read_json(self.health_file)
        
        health[str(source_id)].update(updates)
        health[str(source_id)]['updated_at'] = datetime.utcnow().isoformat()
        
        self._write_json(self.health_file, health)
    
    def record_job_execution(self, source_id: int, success: bool, 
                           documents_found: int = 0, 
                           execution_time: Optional[int] = None,
                           error: Optional[str] = None):
        """Record a job execution and update health metrics"""
        metrics = self.get_health_metrics(source_id)
        
        # Update counters
        metrics['total_executions'] += 1
        
        if success:
            metrics['successful_executions'] += 1
            metrics['consecutive_failures'] = 0
            metrics['last_success_at'] = datetime.utcnow().isoformat()
        else:
            metrics['failed_executions'] += 1
            metrics['consecutive_failures'] += 1
            metrics['last_failure_at'] = datetime.utcnow().isoformat()
        
        # Update document stats
        metrics['total_documents_found'] += documents_found
        if metrics['total_executions'] > 0:
            metrics['average_documents_per_run'] = metrics['total_documents_found'] // metrics['total_executions']
        
        # Update execution time
        if execution_time is not None:
            if metrics['average_execution_time'] is None:
                metrics['average_execution_time'] = execution_time
            else:
                # Running average
                metrics['average_execution_time'] = (
                    (metrics['average_execution_time'] * (metrics['total_executions'] - 1) + execution_time)
                    // metrics['total_executions']
                )
        
        self.update_health_metrics(source_id, metrics)
    
    def check_alerts(self, threshold: int = 3) -> List[Dict[str, Any]]:
        """Check for sources that need attention"""
        health = self._read_json(self.health_file)
        alerts = []
        
        for source_id, metrics in health.items():
            if metrics.get('consecutive_failures', 0) >= threshold:
                alerts.append({
                    'source_id': int(source_id),
                    'consecutive_failures': metrics['consecutive_failures'],
                    'last_failure_at': metrics.get('last_failure_at'),
                    'message': f"Source {source_id} has failed {metrics['consecutive_failures']} times consecutively"
                })
        
        return alerts
    
    # ==================== UTILITY ====================
    
    def clear_all(self):
        """Clear all storage (for testing)"""
        for file in [self.sources_file, self.jobs_file, self.tracker_file, self.health_file]:
            self._write_json(file, {})
    
    def export_data(self) -> Dict[str, Any]:
        """Export all data"""
        return {
            'sources': self._read_json(self.sources_file),
            'jobs': self._read_json(self.jobs_file),
            'tracker': self._read_json(self.tracker_file),
            'health': self._read_json(self.health_file)
        }

    # ==================== SCRAPING LOGS ====================
    
    def create_scraping_log(self, log_data: Dict[str, Any]) -> int:
        """Create a new scraping log entry"""
        logs = self._read_json(self.logs_file)
        
        # Generate new ID
        log_id = max([int(k) for k in logs.keys()], default=0) + 1
        
        log_data['id'] = log_id
        log_data['created_at'] = datetime.utcnow().isoformat()
        
        logs[str(log_id)] = log_data
        self._write_json(self.logs_file, logs)
        
        return log_id
    
    def get_scraping_log(self, log_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific scraping log"""
        logs = self._read_json(self.logs_file)
        return logs.get(str(log_id))
    
    def update_scraping_log(self, log_id: int, log_data: Dict[str, Any]):
        """Update a scraping log"""
        logs = self._read_json(self.logs_file)
        
        if str(log_id) in logs:
            log_data['updated_at'] = datetime.utcnow().isoformat()
            logs[str(log_id)] = log_data
            self._write_json(self.logs_file, logs)
    
    def get_recent_scraping_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent scraping logs"""
        logs = self._read_json(self.logs_file)
        
        # Convert to list and sort by created_at (newest first)
        log_list = list(logs.values())
        log_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return log_list[:limit]
    
    def get_scraping_logs_for_source(self, source_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Get scraping logs for a specific source"""
        logs = self._read_json(self.logs_file)
        
        # Filter by source_id
        source_logs = [log for log in logs.values() if log.get('source_id') == source_id]
        
        # Sort by created_at (newest first)
        source_logs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return source_logs[:limit]
    
    def clear_old_scraping_logs(self, days: int = 30):
        """Clear logs older than specified days"""
        from datetime import timedelta
        
        logs = self._read_json(self.logs_file)
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Keep only recent logs
        filtered_logs = {
            log_id: log_data
            for log_id, log_data in logs.items()
            if datetime.fromisoformat(log_data.get('created_at', '')) > cutoff_date
        }
        
        self._write_json(self.logs_file, filtered_logs)
