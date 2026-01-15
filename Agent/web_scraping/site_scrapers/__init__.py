"""
Site-specific scrapers for government websites
Each scraper is optimized for specific government site structures
"""

from .base_scraper import BaseScraper
from .moe_scraper import MoEScraper
from .ugc_scraper import UGCScraper
from .aicte_scraper import AICTEScraper

# Scraper registry for easy access
SCRAPER_REGISTRY = {
    'moe': MoEScraper,
    'ministry_of_education': MoEScraper,
    'ugc': UGCScraper,
    'university_grants_commission': UGCScraper,
    'aicte': AICTEScraper,
    'all_india_council_technical_education': AICTEScraper,
    'generic': BaseScraper,
    'default': BaseScraper
}

def get_scraper_for_site(site_type: str) -> BaseScraper:
    """
    Get appropriate scraper for a site type
    
    Args:
        site_type: Type of site (moe, ugc, aicte, etc.)
        
    Returns:
        Scraper instance
    """
    site_type_lower = site_type.lower().replace(' ', '_')
    
    scraper_class = SCRAPER_REGISTRY.get(site_type_lower, BaseScraper)
    return scraper_class()

def get_available_scrapers() -> dict:
    """Get list of available scrapers"""
    return {
        'moe': 'Ministry of Education',
        'ugc': 'University Grants Commission', 
        'aicte': 'All India Council for Technical Education',
        'generic': 'Generic Government Site'
    }

__all__ = [
    'BaseScraper',
    'MoEScraper', 
    'UGCScraper',
    'AICTEScraper',
    'get_scraper_for_site',
    'get_available_scrapers',
    'SCRAPER_REGISTRY'
]