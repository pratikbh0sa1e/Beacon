"""
Health Monitor for tracking scraping source health and alerting on failures
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class HealthMonitor:
    """Track scraping success rates and alert on failures"""
    
    def __init__(self, storage, alert_threshold: int = 3):
        """
        Initialize health monitor
        
        Args:
            storage: LocalStorage instance for health metrics
            alert_threshold: Number of consecutive failures before alerting
        """
        self.storage = storage
        self.alert_threshold = alert_threshold
    
    def record_job_execution(self,
                            source_id: int,
                            status: str,
                            documents_found: int = 0,
                            execution_time: Optional[int] = None,
                            error: Optional[str] = None) -> None:
        """
        Record execution result and update health metrics
        
        Args:
            source_id: Source ID
            status: Job status ('success', 'failed', 'partial')
            documents_found: Number of documents found
            execution_time: Execution time in seconds
            error: Error message if failed
        """
        success = status == 'success'
        
        logger.info(
            f"Recording job execution for source {source_id}: "
            f"status={status}, docs={documents_found}, time={execution_time}s"
        )
        
        # Record in storage (which updates health metrics)
        self.storage.record_job_execution(
            source_id=source_id,
            success=success,
            documents_found=documents_found,
            execution_time=execution_time,
            error=error
        )
        
        # Check if we need to alert
        if not success:
            metrics = self.get_source_health(source_id)
            if metrics['consecutive_failures'] >= self.alert_threshold:
                self._trigger_alert(source_id, metrics, error)
    
    def get_source_health(self, source_id: int) -> Dict[str, Any]:
        """
        Get health metrics for a source
        
        Args:
            source_id: Source ID
        
        Returns:
            Dict with health metrics:
                - success_rate: Percentage of successful executions
                - last_success: Timestamp of last successful execution
                - last_failure: Timestamp of last failed execution
                - consecutive_failures: Number of consecutive failures
                - total_executions: Total number of executions
                - average_execution_time: Average execution time in seconds
                - average_documents_per_run: Average documents found per run
        """
        metrics = self.storage.get_health_metrics(source_id)
        
        # Calculate success rate
        if metrics['total_executions'] > 0:
            success_rate = (metrics['successful_executions'] / metrics['total_executions']) * 100
        else:
            success_rate = 0.0
        
        return {
            'source_id': source_id,
            'success_rate': round(success_rate, 2),
            'last_success': metrics.get('last_success_at'),
            'last_failure': metrics.get('last_failure_at'),
            'consecutive_failures': metrics.get('consecutive_failures', 0),
            'total_executions': metrics.get('total_executions', 0),
            'successful_executions': metrics.get('successful_executions', 0),
            'failed_executions': metrics.get('failed_executions', 0),
            'average_execution_time': metrics.get('average_execution_time'),
            'average_documents_per_run': metrics.get('average_documents_per_run'),
            'total_documents_found': metrics.get('total_documents_found', 0),
            'health_status': self._calculate_health_status(metrics),
            'updated_at': metrics.get('updated_at')
        }
    
    def _calculate_health_status(self, metrics: Dict[str, Any]) -> str:
        """
        Calculate overall health status
        
        Args:
            metrics: Health metrics
        
        Returns:
            Health status: 'healthy', 'warning', 'critical', 'unknown'
        """
        total = metrics.get('total_executions', 0)
        
        if total == 0:
            return 'unknown'
        
        consecutive_failures = metrics.get('consecutive_failures', 0)
        success_rate = (metrics.get('successful_executions', 0) / total) * 100
        
        # Critical: consecutive failures at or above threshold
        if consecutive_failures >= self.alert_threshold:
            return 'critical'
        
        # Warning: some failures or low success rate
        if consecutive_failures > 0 or success_rate < 80:
            return 'warning'
        
        # Healthy: no recent failures and good success rate
        return 'healthy'
    
    def check_alerts(self) -> List[Dict[str, Any]]:
        """
        Check for sources that need attention
        
        Returns:
            List of alerts for sources with repeated failures
        """
        alerts = self.storage.check_alerts(threshold=self.alert_threshold)
        
        if alerts:
            logger.warning(f"Found {len(alerts)} sources requiring attention")
        
        return alerts
    
    def _trigger_alert(self, source_id: int, metrics: Dict[str, Any], error: Optional[str] = None):
        """
        Trigger an alert for a failing source
        
        Args:
            source_id: Source ID
            metrics: Health metrics
            error: Error message
        """
        alert_message = (
            f"ALERT: Source {source_id} has failed {metrics['consecutive_failures']} times consecutively. "
            f"Last failure: {metrics.get('last_failure_at')}. "
        )
        
        if error:
            alert_message += f"Error: {error}"
        
        logger.error(alert_message)
        
        # In a real system, this would send notifications (email, Slack, etc.)
        # For now, we just log it
    
    def should_retry(self, source_id: int, attempt: int) -> bool:
        """
        Determine if job should be retried based on history
        
        Args:
            source_id: Source ID
            attempt: Current retry attempt number (0-indexed)
        
        Returns:
            True if should retry
        """
        # Always allow first 3 retries
        if attempt < 3:
            return True
        
        # Check health metrics for additional context
        metrics = self.get_source_health(source_id)
        
        # If source has been consistently failing, don't retry indefinitely
        if metrics['consecutive_failures'] >= self.alert_threshold * 2:
            logger.warning(
                f"Source {source_id} has too many consecutive failures "
                f"({metrics['consecutive_failures']}), stopping retries"
            )
            return False
        
        return True
    
    def get_all_source_health(self) -> List[Dict[str, Any]]:
        """
        Get health metrics for all sources
        
        Returns:
            List of health metrics for all sources
        """
        # Get all sources from storage
        sources = self.storage.list_sources()
        
        health_reports = []
        for source in sources:
            source_id = source['id']
            health = self.get_source_health(source_id)
            health['source_name'] = source.get('name', f'Source {source_id}')
            health['source_url'] = source.get('url')
            health_reports.append(health)
        
        # Sort by health status (critical first)
        status_priority = {'critical': 0, 'warning': 1, 'healthy': 2, 'unknown': 3}
        health_reports.sort(key=lambda x: status_priority.get(x['health_status'], 4))
        
        return health_reports
    
    def get_health_summary(self) -> Dict[str, Any]:
        """
        Get overall health summary across all sources
        
        Returns:
            Dict with summary statistics
        """
        all_health = self.get_all_source_health()
        
        if not all_health:
            return {
                'total_sources': 0,
                'healthy': 0,
                'warning': 0,
                'critical': 0,
                'unknown': 0,
                'overall_status': 'unknown'
            }
        
        # Count by status
        status_counts = {
            'healthy': 0,
            'warning': 0,
            'critical': 0,
            'unknown': 0
        }
        
        for health in all_health:
            status = health['health_status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Determine overall status
        if status_counts['critical'] > 0:
            overall_status = 'critical'
        elif status_counts['warning'] > 0:
            overall_status = 'warning'
        elif status_counts['healthy'] > 0:
            overall_status = 'healthy'
        else:
            overall_status = 'unknown'
        
        return {
            'total_sources': len(all_health),
            'healthy': status_counts['healthy'],
            'warning': status_counts['warning'],
            'critical': status_counts['critical'],
            'unknown': status_counts['unknown'],
            'overall_status': overall_status,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def reset_health_metrics(self, source_id: int):
        """
        Reset health metrics for a source (useful after fixing issues)
        
        Args:
            source_id: Source ID
        """
        logger.info(f"Resetting health metrics for source {source_id}")
        
        self.storage.update_health_metrics(source_id, {
            'consecutive_failures': 0,
            'last_failure_at': None
        })
    
    def log_recovery(self, source_id: int, retry_attempt: int):
        """
        Log successful recovery after failures
        
        Args:
            source_id: Source ID
            retry_attempt: Which retry attempt succeeded
        """
        logger.info(
            f"Source {source_id} recovered successfully on retry attempt {retry_attempt}"
        )
        
        # This is automatically handled by record_job_execution when status='success'
        # But we log it explicitly for visibility
    
    def get_failing_sources(self) -> List[Dict[str, Any]]:
        """
        Get list of sources that are currently failing
        
        Returns:
            List of sources with critical health status
        """
        all_health = self.get_all_source_health()
        
        failing = [
            health for health in all_health
            if health['health_status'] == 'critical'
        ]
        
        return failing
    
    def get_performance_metrics(self, source_id: int) -> Dict[str, Any]:
        """
        Get performance metrics for a source
        
        Args:
            source_id: Source ID
        
        Returns:
            Dict with performance metrics
        """
        health = self.get_source_health(source_id)
        
        return {
            'source_id': source_id,
            'average_execution_time': health['average_execution_time'],
            'average_documents_per_run': health['average_documents_per_run'],
            'total_documents_found': health['total_documents_found'],
            'success_rate': health['success_rate'],
            'total_executions': health['total_executions']
        }
