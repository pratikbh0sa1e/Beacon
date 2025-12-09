"""
Retry utilities with exponential backoff for web scraping
"""
import time
import logging
from typing import Callable, Any, Optional, Type, Tuple
from functools import wraps
import requests

logger = logging.getLogger(__name__)


class RetriableError(Exception):
    """Base exception for errors that should trigger a retry"""
    pass


class NetworkError(RetriableError):
    """Network-related errors that should be retried"""
    pass


class TimeoutError(RetriableError):
    """Timeout errors that should be retried"""
    pass


class HTTPError(RetriableError):
    """HTTP errors that should be retried (5xx, some 4xx)"""
    pass


def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    retriable_exceptions: Tuple[Type[Exception], ...] = None
) -> Any:
    """
    Retry a function with exponential backoff
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds (default: 1s)
        max_delay: Maximum delay in seconds (default: 60s)
        exponential_base: Base for exponential calculation (default: 2)
        retriable_exceptions: Tuple of exception types to retry on
    
    Returns:
        Result of the function call
    
    Raises:
        Last exception if all retries fail
    
    Example:
        result = retry_with_backoff(lambda: scraper.scrape_page(url))
    """
    if retriable_exceptions is None:
        retriable_exceptions = (
            RetriableError,
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.HTTPError
        )
    
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            result = func()
            
            # Log recovery if this was a retry
            if attempt > 0:
                logger.info(f"Function succeeded on retry attempt {attempt + 1}/{max_retries}")
            
            return result
        
        except retriable_exceptions as e:
            last_exception = e
            
            if attempt == max_retries - 1:
                # Last attempt failed
                logger.error(
                    f"Function failed after {max_retries} attempts. "
                    f"Last error: {str(e)}"
                )
                raise
            
            # Calculate delay with exponential backoff
            delay = min(base_delay * (exponential_base ** attempt), max_delay)
            
            logger.warning(
                f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}. "
                f"Retrying in {delay:.1f}s..."
            )
            
            time.sleep(delay)
    
    # Should never reach here, but just in case
    if last_exception:
        raise last_exception


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    exponential_base: float = 2.0
):
    """
    Decorator for adding retry logic with exponential backoff to functions
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        exponential_base: Base for exponential calculation
    
    Example:
        @with_retry(max_retries=3, base_delay=1.0)
        def scrape_page(url):
            return requests.get(url)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return retry_with_backoff(
                lambda: func(*args, **kwargs),
                max_retries=max_retries,
                base_delay=base_delay,
                exponential_base=exponential_base
            )
        return wrapper
    return decorator


class RetryContext:
    """Context manager for retry operations with tracking"""
    
    def __init__(self, 
                 operation_name: str,
                 max_retries: int = 3,
                 base_delay: float = 1.0):
        """
        Initialize retry context
        
        Args:
            operation_name: Name of the operation for logging
            max_retries: Maximum retry attempts
            base_delay: Initial delay in seconds
        """
        self.operation_name = operation_name
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.attempt = 0
        self.total_delay = 0.0
        self.errors = []
    
    def should_retry(self) -> bool:
        """Check if should retry"""
        return self.attempt < self.max_retries
    
    def record_failure(self, error: Exception):
        """Record a failure"""
        self.errors.append({
            'attempt': self.attempt,
            'error': str(error),
            'error_type': type(error).__name__
        })
    
    def wait_before_retry(self):
        """Wait with exponential backoff before next retry"""
        if self.attempt > 0:
            delay = self.base_delay * (2 ** (self.attempt - 1))
            logger.info(
                f"{self.operation_name}: Waiting {delay:.1f}s before retry "
                f"(attempt {self.attempt + 1}/{self.max_retries})"
            )
            time.sleep(delay)
            self.total_delay += delay
    
    def increment_attempt(self):
        """Increment attempt counter"""
        self.attempt += 1
    
    def get_summary(self) -> dict:
        """Get summary of retry attempts"""
        return {
            'operation': self.operation_name,
            'total_attempts': self.attempt,
            'max_retries': self.max_retries,
            'total_delay': self.total_delay,
            'errors': self.errors
        }


def is_retriable_http_error(status_code: int) -> bool:
    """
    Determine if an HTTP status code should trigger a retry
    
    Args:
        status_code: HTTP status code
    
    Returns:
        True if should retry
    """
    # Retry on server errors (5xx)
    if 500 <= status_code < 600:
        return True
    
    # Retry on specific client errors
    retriable_4xx = [
        408,  # Request Timeout
        429,  # Too Many Requests
        499   # Client Closed Request (nginx)
    ]
    
    if status_code in retriable_4xx:
        return True
    
    return False


def classify_error(error: Exception) -> str:
    """
    Classify an error for retry logic
    
    Args:
        error: Exception to classify
    
    Returns:
        Error category: 'network', 'timeout', 'http', 'other'
    """
    if isinstance(error, (requests.exceptions.ConnectionError, 
                         requests.exceptions.ConnectTimeout)):
        return 'network'
    
    if isinstance(error, (requests.exceptions.Timeout,
                         requests.exceptions.ReadTimeout)):
        return 'timeout'
    
    if isinstance(error, requests.exceptions.HTTPError):
        return 'http'
    
    return 'other'


def calculate_backoff_delay(
    attempt: int,
    base_delay: float = 1.0,
    exponential_base: float = 2.0,
    max_delay: float = 60.0,
    jitter: bool = False
) -> float:
    """
    Calculate delay for exponential backoff
    
    Args:
        attempt: Current attempt number (0-indexed)
        base_delay: Base delay in seconds
        exponential_base: Base for exponential calculation
        max_delay: Maximum delay in seconds
        jitter: Whether to add random jitter
    
    Returns:
        Delay in seconds
    """
    delay = base_delay * (exponential_base ** attempt)
    delay = min(delay, max_delay)
    
    if jitter:
        import random
        # Add up to 25% jitter
        jitter_amount = delay * 0.25 * random.random()
        delay += jitter_amount
    
    return delay


class RetryStats:
    """Track retry statistics across operations"""
    
    def __init__(self):
        self.total_operations = 0
        self.successful_first_try = 0
        self.successful_after_retry = 0
        self.failed_after_retries = 0
        self.total_retries = 0
        self.total_delay = 0.0
    
    def record_success(self, attempts: int, delay: float):
        """Record a successful operation"""
        self.total_operations += 1
        
        if attempts == 1:
            self.successful_first_try += 1
        else:
            self.successful_after_retry += 1
            self.total_retries += (attempts - 1)
            self.total_delay += delay
    
    def record_failure(self, attempts: int, delay: float):
        """Record a failed operation"""
        self.total_operations += 1
        self.failed_after_retries += 1
        self.total_retries += attempts
        self.total_delay += delay
    
    def get_stats(self) -> dict:
        """Get retry statistics"""
        if self.total_operations == 0:
            return {
                'total_operations': 0,
                'success_rate': 0.0,
                'average_retries': 0.0,
                'average_delay': 0.0
            }
        
        success_rate = (
            (self.successful_first_try + self.successful_after_retry) / 
            self.total_operations * 100
        )
        
        avg_retries = self.total_retries / self.total_operations
        avg_delay = self.total_delay / self.total_operations
        
        return {
            'total_operations': self.total_operations,
            'successful_first_try': self.successful_first_try,
            'successful_after_retry': self.successful_after_retry,
            'failed_after_retries': self.failed_after_retries,
            'success_rate': round(success_rate, 2),
            'average_retries': round(avg_retries, 2),
            'average_delay': round(avg_delay, 2),
            'total_delay': round(self.total_delay, 2)
        }
