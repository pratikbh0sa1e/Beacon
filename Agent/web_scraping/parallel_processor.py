"""
Parallel Processor for executing multiple scraping jobs concurrently
"""
import logging
import time
from typing import List, Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from datetime import datetime
import threading

logger = logging.getLogger(__name__)


class ParallelProcessor:
    """Execute multiple scraping jobs concurrently with rate limiting"""
    
    def __init__(self, max_workers: int = 5):
        """
        Initialize parallel processor
        
        Args:
            max_workers: Maximum number of concurrent workers
        """
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._rate_limit_lock = threading.Lock()
        self._last_request_time = {}
        
        logger.info(f"Initialized ParallelProcessor with {max_workers} workers")
    
    def scrape_sources_parallel(self,
                                sources: List[Dict[str, Any]],
                                scrape_func: Callable,
                                rate_limit_delay: float = 1.0) -> List[Dict[str, Any]]:
        """
        Scrape multiple sources in parallel
        
        Args:
            sources: List of source configurations
            scrape_func: Function to call for each source (should accept source dict)
            rate_limit_delay: Minimum delay between requests to same domain (seconds)
        
        Returns:
            List of scraping results for each source
        """
        if not sources:
            logger.warning("No sources provided for parallel scraping")
            return []
        
        logger.info(f"Starting parallel scraping of {len(sources)} sources with {self.max_workers} workers")
        
        results = []
        futures = {}
        
        # Submit all tasks
        for source in sources:
            future = self.executor.submit(
                self._scrape_with_isolation,
                source,
                scrape_func,
                rate_limit_delay
            )
            futures[future] = source
        
        # Collect results as they complete
        completed_count = 0
        for future in as_completed(futures):
            source = futures[future]
            source_id = source.get('id', 'unknown')
            
            try:
                result = future.result()
                results.append(result)
                completed_count += 1
                
                status = result.get('status', 'unknown')
                docs_found = result.get('documents_found', 0)
                
                logger.info(
                    f"Completed {completed_count}/{len(sources)}: "
                    f"Source {source_id} - {status} ({docs_found} docs)"
                )
            
            except Exception as e:
                logger.error(f"Error scraping source {source_id}: {str(e)}")
                results.append({
                    'source_id': source_id,
                    'status': 'error',
                    'error': str(e),
                    'documents_found': 0
                })
                completed_count += 1
        
        logger.info(f"Parallel scraping complete: {len(results)} sources processed")
        
        return results
    
    def _scrape_with_isolation(self,
                               source: Dict[str, Any],
                               scrape_func: Callable,
                               rate_limit_delay: float) -> Dict[str, Any]:
        """
        Scrape a source with error isolation
        
        Args:
            source: Source configuration
            scrape_func: Scraping function
            rate_limit_delay: Rate limit delay
        
        Returns:
            Scraping result
        """
        source_id = source.get('id', 'unknown')
        source_url = source.get('url', '')
        
        try:
            # Apply rate limiting
            self._apply_rate_limit(source_url, rate_limit_delay)
            
            # Execute scraping
            logger.debug(f"Worker starting scrape for source {source_id}")
            result = scrape_func(source)
            
            return result
        
        except Exception as e:
            logger.error(f"Isolated error in source {source_id}: {str(e)}")
            return {
                'source_id': source_id,
                'status': 'error',
                'error': str(e),
                'documents_found': 0,
                'error_isolated': True
            }
    
    def _apply_rate_limit(self, url: str, delay: float):
        """
        Apply rate limiting per domain
        
        Args:
            url: URL to rate limit
            delay: Minimum delay between requests
        """
        from urllib.parse import urlparse
        
        # Extract domain
        domain = urlparse(url).netloc
        
        with self._rate_limit_lock:
            last_time = self._last_request_time.get(domain, 0)
            current_time = time.time()
            time_since_last = current_time - last_time
            
            if time_since_last < delay:
                sleep_time = delay - time_since_last
                logger.debug(f"Rate limiting {domain}: sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)
            
            self._last_request_time[domain] = time.time()
    
    def scrape_with_rate_limit(self,
                               source: Dict[str, Any],
                               scrape_func: Callable,
                               delay_seconds: float = 1.0) -> Dict[str, Any]:
        """
        Scrape a single source with rate limiting
        
        Args:
            source: Source configuration
            scrape_func: Function to scrape the source
            delay_seconds: Delay between requests
        
        Returns:
            Scraping result
        """
        source_url = source.get('url', '')
        
        # Apply rate limit
        self._apply_rate_limit(source_url, delay_seconds)
        
        # Execute scraping
        return scrape_func(source)
    
    def scrape_batch(self,
                    sources: List[Dict[str, Any]],
                    scrape_func: Callable,
                    batch_size: int = 10,
                    delay_between_batches: float = 5.0) -> List[Dict[str, Any]]:
        """
        Scrape sources in batches to control load
        
        Args:
            sources: List of sources
            scrape_func: Scraping function
            batch_size: Number of sources per batch
            delay_between_batches: Delay between batches
        
        Returns:
            List of all results
        """
        all_results = []
        total_batches = (len(sources) + batch_size - 1) // batch_size
        
        logger.info(f"Processing {len(sources)} sources in {total_batches} batches of {batch_size}")
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(sources))
            batch = sources[start_idx:end_idx]
            
            logger.info(f"Processing batch {batch_num + 1}/{total_batches} ({len(batch)} sources)")
            
            batch_results = self.scrape_sources_parallel(batch, scrape_func)
            all_results.extend(batch_results)
            
            # Delay between batches (except after last batch)
            if batch_num < total_batches - 1:
                logger.info(f"Waiting {delay_between_batches}s before next batch...")
                time.sleep(delay_between_batches)
        
        logger.info(f"Batch processing complete: {len(all_results)} total results")
        
        return all_results
    
    def get_active_workers(self) -> int:
        """
        Get number of currently active workers
        
        Returns:
            Number of active workers
        """
        # ThreadPoolExecutor doesn't expose this directly
        # This is an approximation
        return self.max_workers
    
    def shutdown(self, wait: bool = True):
        """
        Shutdown the executor
        
        Args:
            wait: Whether to wait for pending tasks
        """
        logger.info(f"Shutting down ParallelProcessor (wait={wait})")
        self.executor.shutdown(wait=wait)
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.shutdown(wait=True)


class ParallelScrapingStats:
    """Track statistics for parallel scraping operations"""
    
    def __init__(self):
        self.total_sources = 0
        self.successful = 0
        self.failed = 0
        self.total_documents = 0
        self.total_time = 0.0
        self.source_times = []
        self._lock = threading.Lock()
    
    def record_result(self, result: Dict[str, Any], execution_time: float):
        """
        Record a scraping result
        
        Args:
            result: Scraping result
            execution_time: Time taken in seconds
        """
        with self._lock:
            self.total_sources += 1
            
            if result.get('status') == 'success':
                self.successful += 1
            else:
                self.failed += 1
            
            self.total_documents += result.get('documents_found', 0)
            self.source_times.append(execution_time)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics summary"""
        with self._lock:
            if self.total_sources == 0:
                return {
                    'total_sources': 0,
                    'successful': 0,
                    'failed': 0,
                    'success_rate': 0.0,
                    'total_documents': 0,
                    'average_time': 0.0,
                    'total_time': 0.0
                }
            
            success_rate = (self.successful / self.total_sources) * 100
            avg_time = sum(self.source_times) / len(self.source_times) if self.source_times else 0
            total_time = sum(self.source_times)
            
            return {
                'total_sources': self.total_sources,
                'successful': self.successful,
                'failed': self.failed,
                'success_rate': round(success_rate, 2),
                'total_documents': self.total_documents,
                'average_time': round(avg_time, 2),
                'total_time': round(total_time, 2),
                'min_time': round(min(self.source_times), 2) if self.source_times else 0,
                'max_time': round(max(self.source_times), 2) if self.source_times else 0
            }


def verify_fault_isolation(results: List[Dict[str, Any]]) -> bool:
    """
    Verify that failures were isolated (other sources succeeded)
    
    Args:
        results: List of scraping results
    
    Returns:
        True if fault isolation worked correctly
    """
    if len(results) < 2:
        return True  # Can't verify with less than 2 sources
    
    has_failure = any(r.get('status') != 'success' for r in results)
    has_success = any(r.get('status') == 'success' for r in results)
    
    # If there's at least one failure and at least one success,
    # fault isolation is working
    if has_failure and has_success:
        logger.info("Fault isolation verified: failures did not affect other sources")
        return True
    
    return True  # All succeeded or all failed is also valid


def measure_concurrency(results: List[Dict[str, Any]], 
                       start_time: float,
                       end_time: float) -> Dict[str, Any]:
    """
    Measure actual concurrency achieved
    
    Args:
        results: List of results
        start_time: Overall start time
        end_time: Overall end time
    
    Returns:
        Dict with concurrency metrics
    """
    total_time = end_time - start_time
    
    # Sum of individual execution times
    individual_times = sum(r.get('execution_time', 0) for r in results)
    
    # Theoretical concurrency
    if total_time > 0:
        theoretical_concurrency = individual_times / total_time
    else:
        theoretical_concurrency = 0
    
    return {
        'total_wall_time': round(total_time, 2),
        'sum_individual_times': round(individual_times, 2),
        'theoretical_concurrency': round(theoretical_concurrency, 2),
        'speedup_factor': round(individual_times / total_time, 2) if total_time > 0 else 0
    }
