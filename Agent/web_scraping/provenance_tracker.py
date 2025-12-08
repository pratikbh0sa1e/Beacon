"""
Provenance tracking for scraped documents
"""
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ProvenanceTracker:
    """Track provenance (source, credibility, history) of scraped documents"""
    
    # Credibility scores for known government domains
    CREDIBILITY_SCORES = {
        "education.gov.in": 10,  # Ministry of Education
        "ugc.ac.in": 9,  # University Grants Commission
        "aicte-india.org": 9,  # AICTE
        "mhrd.gov.in": 10,  # Ministry of HRD (old domain)
        "nic.in": 8,  # National Informatics Centre
        "india.gov.in": 10,  # National Portal of India
        "pib.gov.in": 9,  # Press Information Bureau
        "egazette.nic.in": 10,  # Official Gazette
        "default": 5  # Unknown sources
    }
    
    def __init__(self):
        """Initialize provenance tracker"""
        pass
    
    def create_provenance_record(self,
                                url: str,
                                document_title: str,
                                source_page: Optional[str] = None,
                                scraped_at: Optional[str] = None,
                                additional_metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Create a provenance record for a scraped document
        
        Args:
            url: Document URL
            document_title: Title of the document
            source_page: Page where document was found
            scraped_at: Timestamp of scraping
            additional_metadata: Any additional metadata
        
        Returns:
            Provenance record dict
        """
        if scraped_at is None:
            scraped_at = datetime.utcnow().isoformat()
        
        # Extract domain
        domain = self._extract_domain(url)
        
        # Calculate credibility score
        credibility = self._calculate_credibility(domain)
        
        # Determine source type
        source_type = self._determine_source_type(domain)
        
        provenance = {
            "source_url": url,
            "source_page": source_page or url,
            "source_domain": domain,
            "source_type": source_type,
            "document_title": document_title,
            "scraped_at": scraped_at,
            "credibility_score": credibility,
            "ingestion_method": "web_scraping",
            "verified": self._is_verified_source(domain),
            "metadata": additional_metadata or {}
        }
        
        logger.info(f"Created provenance record for {document_title} from {domain}")
        return provenance
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        from urllib.parse import urlparse
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            
            return domain
        
        except Exception as e:
            logger.error(f"Error extracting domain from {url}: {str(e)}")
            return "unknown"
    
    def _calculate_credibility(self, domain: str) -> int:
        """
        Calculate credibility score for a domain
        
        Args:
            domain: Domain name
        
        Returns:
            Credibility score (1-10)
        """
        # Check exact match
        if domain in self.CREDIBILITY_SCORES:
            return self.CREDIBILITY_SCORES[domain]
        
        # Check if it's a .gov.in domain
        if domain.endswith('.gov.in'):
            return 9
        
        # Check if it's a .ac.in domain (academic)
        if domain.endswith('.ac.in'):
            return 8
        
        # Check if it's a .edu.in domain
        if domain.endswith('.edu.in'):
            return 8
        
        # Check if it's a .nic.in domain
        if domain.endswith('.nic.in'):
            return 8
        
        # Default score
        return self.CREDIBILITY_SCORES["default"]
    
    def _determine_source_type(self, domain: str) -> str:
        """
        Determine the type of source
        
        Args:
            domain: Domain name
        
        Returns:
            Source type string
        """
        if domain.endswith('.gov.in'):
            return "government"
        elif domain.endswith('.ac.in') or domain.endswith('.edu.in'):
            return "academic"
        elif domain.endswith('.nic.in'):
            return "government_it"
        elif 'ministry' in domain.lower() or 'moe' in domain.lower():
            return "ministry"
        else:
            return "other"
    
    def _is_verified_source(self, domain: str) -> bool:
        """
        Check if source is verified/trusted
        
        Args:
            domain: Domain name
        
        Returns:
            True if verified, False otherwise
        """
        # Verified if it's in our known list or is a .gov.in domain
        return (domain in self.CREDIBILITY_SCORES or 
                domain.endswith('.gov.in') or
                domain.endswith('.nic.in'))
    
    def enrich_provenance(self, provenance: Dict[str, Any],
                         page_metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Enrich provenance record with additional metadata
        
        Args:
            provenance: Existing provenance record
            page_metadata: Additional metadata from page
        
        Returns:
            Enriched provenance record
        """
        if page_metadata:
            # Add page metadata
            if 'author' in page_metadata:
                provenance['metadata']['author'] = page_metadata['author']
            
            if 'published_date' in page_metadata:
                provenance['metadata']['published_date'] = page_metadata['published_date']
            
            if 'description' in page_metadata:
                provenance['metadata']['description'] = page_metadata['description']
            
            if 'keywords' in page_metadata:
                provenance['metadata']['keywords'] = page_metadata['keywords']
        
        return provenance
    
    def validate_provenance(self, provenance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate provenance record
        
        Args:
            provenance: Provenance record to validate
        
        Returns:
            Validation result
        """
        required_fields = ['source_url', 'source_domain', 'document_title', 'scraped_at']
        
        missing_fields = [field for field in required_fields if field not in provenance]
        
        if missing_fields:
            return {
                "valid": False,
                "missing_fields": missing_fields,
                "message": f"Missing required fields: {', '.join(missing_fields)}"
            }
        
        # Check credibility score
        if provenance.get('credibility_score', 0) < 5:
            return {
                "valid": True,
                "warning": "Low credibility score",
                "message": "Source has low credibility score, manual verification recommended"
            }
        
        return {
            "valid": True,
            "message": "Provenance record is valid"
        }
    
    def get_source_summary(self, domain: str) -> Dict[str, Any]:
        """
        Get summary information about a source domain
        
        Args:
            domain: Domain name
        
        Returns:
            Source summary
        """
        return {
            "domain": domain,
            "credibility_score": self._calculate_credibility(domain),
            "source_type": self._determine_source_type(domain),
            "verified": self._is_verified_source(domain),
            "trust_level": self._get_trust_level(self._calculate_credibility(domain))
        }
    
    def _get_trust_level(self, credibility_score: int) -> str:
        """Convert credibility score to trust level"""
        if credibility_score >= 9:
            return "high"
        elif credibility_score >= 7:
            return "medium"
        elif credibility_score >= 5:
            return "low"
        else:
            return "very_low"
    
    def compare_sources(self, provenance1: Dict[str, Any],
                       provenance2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare two provenance records
        
        Args:
            provenance1: First provenance record
            provenance2: Second provenance record
        
        Returns:
            Comparison result
        """
        return {
            "same_domain": provenance1['source_domain'] == provenance2['source_domain'],
            "credibility_diff": abs(provenance1['credibility_score'] - provenance2['credibility_score']),
            "both_verified": provenance1['verified'] and provenance2['verified'],
            "more_credible": provenance1['source_domain'] if provenance1['credibility_score'] > provenance2['credibility_score'] else provenance2['source_domain']
        }
