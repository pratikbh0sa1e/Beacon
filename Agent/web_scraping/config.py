"""
Configuration settings for web scraping system
"""

class ScrapingConfig:
    """Centralized configuration for web scraping"""
    
    # Document limits
    MAX_DOCUMENTS_PER_SOURCE = 1500  # Maximum documents to scrape from a single source
    
    # Pagination settings
    DEFAULT_MAX_PAGES = 100  # Maximum pages to scrape (will stop at document limit first)
    PAGE_DELAY_SECONDS = 1.0  # Delay between page requests
    
    # Retry settings
    MAX_RETRIES = 3  # Maximum retry attempts for failed requests
    RETRY_DELAY_BASE = 1  # Base delay for exponential backoff (seconds)
    
    # Rate limiting
    RATE_LIMIT_DELAY = 1.0  # Minimum delay between requests (seconds)
    MAX_WORKERS = 5  # Maximum parallel workers for concurrent scraping
    
    # Timeouts
    REQUEST_TIMEOUT = 30  # HTTP request timeout (seconds)
    
    # Health monitoring
    HEALTH_CHECK_INTERVAL = 3600  # Health check interval (seconds)
    ALERT_THRESHOLD = 3  # Alert after N consecutive failures
    
    # Scheduling
    DAILY_SCHEDULE_TIME = "02:00"  # Default daily scrape time
    
    @classmethod
    def set_max_documents(cls, max_docs: int):
        """
        Update the maximum documents per source
        
        Args:
            max_docs: New maximum document limit
        """
        cls.MAX_DOCUMENTS_PER_SOURCE = max_docs
    
    @classmethod
    def get_max_documents(cls) -> int:
        """Get current maximum documents per source"""
        return cls.MAX_DOCUMENTS_PER_SOURCE
    
    @classmethod
    def set_max_pages(cls, max_pages: int):
        """
        Update the maximum pages to scrape
        
        Args:
            max_pages: New maximum page limit
        """
        cls.DEFAULT_MAX_PAGES = max_pages
    
    @classmethod
    def get_config_summary(cls) -> dict:
        """Get summary of current configuration"""
        return {
            'max_documents_per_source': cls.MAX_DOCUMENTS_PER_SOURCE,
            'default_max_pages': cls.DEFAULT_MAX_PAGES,
            'page_delay_seconds': cls.PAGE_DELAY_SECONDS,
            'max_retries': cls.MAX_RETRIES,
            'rate_limit_delay': cls.RATE_LIMIT_DELAY,
            'max_workers': cls.MAX_WORKERS,
            'request_timeout': cls.REQUEST_TIMEOUT,
            'daily_schedule_time': cls.DAILY_SCHEDULE_TIME
        }
