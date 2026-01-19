"""Metadata extraction service for Lazy RAG"""
import logging
import re
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime

# Try to import sklearn, with fallback for deployment issues
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("scikit-learn not available - using simple keyword extraction fallback")

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
import os

# Setup logging
log_dir = Path("Agent/agent_logs")
log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "metadata.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Extract metadata from documents without full embedding"""
    
    def __init__(
        self, 
        provider: Optional[str] = None,
        google_api_key: Optional[str] = None,
        xai_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        openrouter_api_key: Optional[str] = None
    ):
        """
        Initialize metadata extractor with multi-provider support
        
        Args:
            provider: LLM provider ("openrouter", "grok", "gemini", "openai") - defaults to env METADATA_LLM_PROVIDER
            google_api_key: Google API key for Gemini
            xai_api_key: xAI API key for Grok
            openai_api_key: OpenAI API key
            openrouter_api_key: OpenRouter API key
        """
        # Get provider from parameter or environment
        self.provider = provider or os.getenv("METADATA_LLM_PROVIDER", "gemini")
        self.fallback_provider = os.getenv("METADATA_FALLBACK_PROVIDER", "gemini")
        
        # Get API keys
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        self.xai_api_key = xai_api_key or os.getenv("XAI_API_KEY")
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.openrouter_api_key = openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
        
        # Initialize LLMs
        self.llm = None
        self.fallback_llm = None
        
        # Initialize primary LLM
        self.llm = self._initialize_llm(self.provider)
        
        # Initialize fallback LLM if different from primary
        if self.fallback_provider != self.provider:
            self.fallback_llm = self._initialize_llm(self.fallback_provider)
        
        if self.llm:
            logger.info(f"Metadata extractor initialized with primary LLM: {self.provider}")
            if self.fallback_llm:
                logger.info(f"Fallback LLM configured: {self.fallback_provider}")
        else:
            logger.warning("No LLM provider configured - metadata extraction will be limited")
    
    def _initialize_llm(self, provider: str):
        """Initialize LLM based on provider"""
        try:
            if provider == "openrouter":
                if not self.openrouter_api_key:
                    logger.warning("OPENROUTER_API_KEY not found - OpenRouter unavailable")
                    return None
                
                # Get model from env or use default
                model = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
                
                logger.info(f"Initializing OpenRouter with model: {model}")
                return ChatOpenAI(
                    model=model,
                    api_key=self.openrouter_api_key,
                    base_url="https://openrouter.ai/api/v1",
                    temperature=0.1,
                    max_tokens=2000,
                    default_headers={
                        "HTTP-Referer": "https://github.com/your-repo",  # Optional: for rankings
                        "X-Title": "Document Metadata Extractor"  # Optional: show in rankings
                    }
                )
            
            elif provider == "grok":
                if not self.xai_api_key:
                    logger.warning("XAI_API_KEY not found - Grok unavailable")
                    return None
                
                logger.info("Initializing Grok (xAI) for metadata extraction")
                return ChatOpenAI(
                    model="grok-beta",
                    api_key=self.xai_api_key,
                    base_url="https://api.x.ai/v1",
                    temperature=0.1,
                    max_tokens=2000
                )
            
            elif provider == "gemini":
                if not self.google_api_key:
                    logger.warning("GOOGLE_API_KEY not found - Gemini unavailable")
                    return None
                
                logger.info("Initializing Gemini (gemma-3-12b) for metadata extraction")
                return ChatGoogleGenerativeAI(
                    model="gemma-3-12b",
                    google_api_key=self.google_api_key,
                    temperature=0.1
                )
            
            elif provider == "openai":
                if not self.openai_api_key:
                    logger.warning("OPENAI_API_KEY not found - OpenAI unavailable")
                    return None
                
                logger.info("Initializing OpenAI for metadata extraction")
                return ChatOpenAI(
                    model="gpt-4o-mini",
                    api_key=self.openai_api_key,
                    temperature=0.1,
                    max_tokens=2000
                )
            
            elif provider == "ollama":
                ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
                ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")
                
                logger.info(f"Initializing Ollama with model: {ollama_model}")
                return ChatOpenAI(
                    model=ollama_model,
                    base_url=f"{ollama_base_url}/v1",
                    api_key="ollama",  # Ollama doesn't need real API key
                    temperature=0.1,
                    max_tokens=2000
                )
            
            else:
                logger.error(f"Unknown provider: {provider}")
                return None
                
        except Exception as e:
            logger.error(f"Error initializing {provider}: {str(e)}")
            return None
    
    def extract_metadata(self, text: str, filename: str) -> Dict:
        """
        Extract comprehensive metadata from document
        
        Args:
            text: Full document text
            filename: Original filename
        
        Returns:
            Dictionary with extracted metadata
        """
        logger.info(f"Extracting metadata for: {filename}")
        
        metadata = {
            "title": None,
            "department": None,
            "document_type": None,
            "date_published": None,
            "keywords": [],
            "summary": None,
            "key_topics": [],
            "entities": {},
            "bm25_keywords": None,
            "text_length": len(text)
        }
        
        # Step 1: Parse filename
        filename_metadata = self._parse_filename(filename)
        metadata.update(filename_metadata)
        
        # Step 2: Extract from first page
        first_page = text[:3000]  # First ~3000 chars
        first_page_metadata = self._extract_from_first_page(first_page)
        metadata.update({k: v for k, v in first_page_metadata.items() if v})
        
        # Step 3: Extract TF-IDF keywords
        keywords = self._extract_tfidf_keywords(text, top_n=20)
        metadata["keywords"] = keywords
        metadata["bm25_keywords"] = " ".join(keywords)
        
        # Step 4: LLM-based extraction (if available)
        if self.llm:
            llm_metadata = self._llm_extract_metadata(first_page, filename)
            metadata.update({k: v for k, v in llm_metadata.items() if v})
        
        logger.info(f"Metadata extracted: title={metadata.get('title')}, dept={metadata.get('department')}")
        return metadata
    
    def _parse_filename(self, filename: str) -> Dict:
        """Extract metadata from filename"""
        metadata = {}
        
        # Remove extension
        name = Path(filename).stem
        
        # Try to extract year (4 digits)
        year_match = re.search(r'(19|20)\d{2}', name)
        if year_match:
            try:
                year = int(year_match.group())
                metadata["date_published"] = datetime(year, 1, 1).date()
            except:
                pass
        
        # Try to extract department (common patterns)
        dept_patterns = [
            r'MoE|Ministry of Education',
            r'MoH|Ministry of Health',
            r'MoF|Ministry of Finance',
            r'MoD|Ministry of Defence',
            r'MHA|Ministry of Home Affairs'
        ]
        for pattern in dept_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                metadata["department"] = re.search(pattern, name, re.IGNORECASE).group()
                break
        
        # Use filename as fallback title
        metadata["title"] = name.replace('_', ' ').replace('-', ' ')
        
        return metadata
    
    def _extract_from_first_page(self, text: str) -> Dict:
        """Extract metadata from first page text"""
        metadata = {}
        
        # Look for title (usually first line or in caps)
        lines = text.split('\n')
        for line in lines[:10]:
            line = line.strip()
            if len(line) > 10 and len(line) < 200:
                # Likely a title
                if line.isupper() or line.istitle():
                    metadata["title"] = line
                    break
        
        # Look for date patterns
        date_patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # DD/MM/YYYY
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY-MM-DD
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    if len(match.groups()) == 3:
                        if match.group(1).isdigit() and len(match.group(1)) == 4:
                            year = int(match.group(1))
                            metadata["date_published"] = datetime(year, 1, 1).date()
                        break
                except:
                    pass
        
        # Look for document type keywords
        doc_types = {
            "policy": ["policy", "policies"],
            "report": ["report", "annual report"],
            "memo": ["memorandum", "memo"],
            "guideline": ["guideline", "guidelines"],
            "regulation": ["regulation", "regulations"],
            "act": ["act", "legislation"]
        }
        
        text_lower = text.lower()
        for doc_type, keywords in doc_types.items():
            if any(kw in text_lower for kw in keywords):
                metadata["document_type"] = doc_type
                break
        
        return metadata
    
    def _extract_tfidf_keywords(self, text: str, top_n: int = 20) -> List[str]:
        """Extract top keywords using TF-IDF with fallback"""
        if not SKLEARN_AVAILABLE:
            # Fallback to simple keyword extraction
            logger.info("Using simple keyword extraction fallback (sklearn not available)")
            return self._simple_keyword_extraction(text, top_n)
        
        try:
            vectorizer = TfidfVectorizer(
                max_features=top_n,
                stop_words='english',
                ngram_range=(1, 2),
                min_df=1,
                max_df=0.8
            )
            
            tfidf_matrix = vectorizer.fit_transform([text])
            feature_names = vectorizer.get_feature_names_out()
            scores = tfidf_matrix.toarray()[0]
            top_indices = scores.argsort()[-top_n:][::-1]
            keywords = [feature_names[i] for i in top_indices if scores[i] > 0]
            
            logger.info(f"Extracted {len(keywords)} TF-IDF keywords")
            return keywords
            
        except Exception as e:
            logger.error(f"Error extracting TF-IDF keywords: {str(e)}")
            logger.info("Falling back to simple keyword extraction")
            return self._simple_keyword_extraction(text, top_n)
    
    def _simple_keyword_extraction(self, text: str, top_n: int = 20) -> List[str]:
        """Simple keyword extraction fallback when sklearn is not available"""
        import re
        from collections import Counter
        
        # Simple stopwords list
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his',
            'her', 'its', 'our', 'their', 'mine', 'yours', 'hers', 'ours', 'theirs', 'from', 'up', 'about', 'into',
            'through', 'during', 'before', 'after', 'above', 'below', 'between', 'among', 'under', 'over'
        }
        
        # Extract words (2+ characters, alphanumeric)
        words = re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())
        
        # Filter out stopwords and get word counts
        filtered_words = [word for word in words if word not in stopwords and len(word) > 2]
        word_counts = Counter(filtered_words)
        
        # Get top keywords
        keywords = [word for word, count in word_counts.most_common(top_n)]
        
        logger.info(f"Extracted {len(keywords)} simple keywords")
        return keywords
    
    def _llm_extract_metadata(self, text: str, filename: str, retry_with_fallback: bool = True) -> Dict:
        """
        Use LLM to extract rich metadata with automatic fallback
        
        Args:
            text: Document text
            filename: Document filename
            retry_with_fallback: If True, retry with fallback LLM on failure
        
        Returns:
            Dictionary with extracted metadata
        """
        prompt = f"""Analyze this document and extract metadata in JSON format.

Document: {filename}
Text: {text[:2000]}

Extract and return ONLY valid JSON:
{{
    "title": "document title",
    "department": "ministry name",
    "document_type": "policy/report/memo/guideline",
    "summary": "2-3 sentence summary",
    "key_topics": ["topic1", "topic2", "topic3"],
    "entities": {{"departments": [], "locations": [], "people": []}}
}}"""

        # Try primary LLM
        if self.llm:
            try:
                logger.info(f"Calling primary LLM ({self.provider}) for metadata extraction...")
                response = self.llm.invoke(prompt)
                
                import json
                response_text = response.content.strip()
                
                # Clean up response
                if response_text.startswith("```"):
                    response_text = response_text.split("```")[1]
                    if response_text.startswith("json"):
                        response_text = response_text[4:]
                
                metadata = json.loads(response_text)
                
                # Validate critical fields
                if metadata.get('title') and metadata.get('summary'):
                    logger.info(f"Primary LLM ({self.provider}) extraction successful")
                    return metadata
                else:
                    logger.warning(f"Primary LLM ({self.provider}) returned incomplete metadata")
                    if not retry_with_fallback or not self.fallback_llm:
                        return metadata
                    
            except Exception as e:
                logger.error(f"Primary LLM ({self.provider}) extraction failed: {str(e)}")
                if not retry_with_fallback or not self.fallback_llm:
                    return {}
        
        # Try fallback LLM if available
        if retry_with_fallback and self.fallback_llm:
            try:
                logger.info(f"Retrying with fallback LLM ({self.fallback_provider})...")
                response = self.fallback_llm.invoke(prompt)
                
                import json
                response_text = response.content.strip()
                
                # Clean up response
                if response_text.startswith("```"):
                    response_text = response_text.split("```")[1]
                    if response_text.startswith("json"):
                        response_text = response_text[4:]
                
                metadata = json.loads(response_text)
                logger.info(f"Fallback LLM ({self.fallback_provider}) extraction successful")
                return metadata
                
            except Exception as e:
                logger.error(f"Fallback LLM ({self.fallback_provider}) extraction failed: {str(e)}")
                return {}
        
        return {}

    def validate_metadata_quality(self, metadata: Dict) -> tuple[bool, str]:
        """
        Validate if extracted metadata meets quality requirements
        
        Args:
            metadata: Extracted metadata dictionary
        
        Returns:
            Tuple of (is_valid, reason)
        """
        require_title = os.getenv("REQUIRE_TITLE", "true").lower() == "true"
        require_summary = os.getenv("REQUIRE_SUMMARY", "true").lower() == "true"
        
        # Check title
        if require_title:
            title = metadata.get('title', '').strip()
            if not title or len(title) < 5:
                return False, "Missing or invalid title"
        
        # Check summary
        if require_summary:
            summary = metadata.get('summary', '').strip()
            if not summary or len(summary) < 20:
                return False, "Missing or invalid summary"
        
        # Check if we have at least some metadata
        if not any([
            metadata.get('title'),
            metadata.get('department'),
            metadata.get('document_type'),
            metadata.get('summary')
        ]):
            return False, "No meaningful metadata extracted"
        
        return True, "Metadata quality acceptable"
