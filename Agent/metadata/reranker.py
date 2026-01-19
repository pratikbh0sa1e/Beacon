"""Document reranker for Lazy RAG - modular design with quota management"""
import logging
from typing import List, Dict
from pathlib import Path
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
import os
from backend.utils.quota_manager import get_quota_manager, QuotaExceededException

# Setup logging
log_dir = Path("Agent/agent_logs")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "reranker.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DocumentReranker:
    """Rerank documents based on query relevance with quota management"""
    
    def __init__(self, provider: str = None, google_api_key: str = None):
        """
        Initialize reranker with multi-provider support and quota management
        
        Args:
            provider: LLM provider ("openrouter", "gemini", "local") - defaults to env RERANKER_PROVIDER
            google_api_key: Google API key (required for gemini provider)
        """
        # Check if cloud-only mode is enabled
        self.cloud_only = os.getenv("CLOUD_ONLY_MODE", "true").lower() == "true"
        
        # Get provider from parameter or environment
        self.provider = provider or os.getenv("RERANKER_PROVIDER", "openrouter" if self.cloud_only else "local")
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        
        # Initialize quota manager
        self.quota_manager = get_quota_manager()
        
        # Force cloud provider in cloud-only mode
        if self.cloud_only and self.provider == "local":
            self.provider = "openrouter"  # Prefer OpenRouter to save Gemini quota
            logger.info("Cloud-only mode enabled - switching reranker from local to OpenRouter")
        
        # Initialize LLM
        self.llm = self._initialize_llm()
        
        if self.llm:
            logger.info(f"Reranker initialized with provider: {self.provider}")
        else:
            logger.warning(f"Reranker provider '{self.provider}' not available, using simple scoring")
    
    def _initialize_llm(self):
        """Initialize LLM based on provider"""
        try:
            if self.provider == "openrouter":
                openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
                if not openrouter_api_key:
                    logger.warning("OPENROUTER_API_KEY not found - OpenRouter unavailable")
                    return None
                
                model = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
                
                logger.info(f"Initializing OpenRouter reranker with model: {model}")
                return ChatOpenAI(
                    model=model,
                    api_key=openrouter_api_key,
                    base_url="https://openrouter.ai/api/v1",
                    temperature=0.1,
                    default_headers={
                        "HTTP-Referer": "https://github.com/your-repo",
                        "X-Title": "Document Reranker"
                    }
                )
            
            elif self.provider == "gemini":
                if not self.google_api_key:
                    logger.warning("GOOGLE_API_KEY not found - Gemini unavailable")
                    return None
                
                logger.info("Initializing Gemini (gemini-1.5-flash) reranker with quota management")
                return ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash",
                    google_api_key=self.google_api_key,
                    temperature=0.1
                )
            
            elif self.provider == "local":
                if self.cloud_only:
                    logger.warning("Local reranker not available in cloud-only mode, falling back to simple scoring")
                    return None
                # Placeholder for future local model implementation
                logger.info("Local reranker selected - will use simple scoring")
                return None
            
            else:
                logger.error(f"Unknown provider: {self.provider}")
                return None
                
        except Exception as e:
            logger.error(f"Error initializing {self.provider}: {str(e)}")
            return None
    
    def rerank(self, query: str, documents: List[Dict], top_k: int = 5) -> List[Dict]:
        """
        Rerank documents based on query relevance
        
        Args:
            query: User query
            documents: List of document metadata dicts
            top_k: Number of top documents to return
        
        Returns:
            Reranked list of documents (top_k)
        """
        logger.info(f"Reranking {len(documents)} documents for query: '{query[:50]}...'")
        
        if self.llm and self.provider in ["gemini", "openrouter"]:
            return self._llm_rerank(query, documents, top_k)
        else:
            return self._simple_rerank(query, documents, top_k)
    
    def _llm_rerank(self, query: str, documents: List[Dict], top_k: int) -> List[Dict]:
        """Rerank using LLM (Gemini or OpenRouter) with quota management"""
        try:
            # Check quota before making API call (only for Gemini)
            if self.provider == "gemini":
                try:
                    allowed, error_msg, quota_info = self.quota_manager.check_quota("gemini_chat", 1)
                    if not allowed:
                        logger.warning(f"Reranker quota exceeded: {error_msg}")
                        logger.info("Falling back to simple reranking due to quota limits")
                        return self._simple_rerank(query, documents, top_k)
                except Exception as e:
                    logger.error(f"Error checking quota: {e}")
                    return self._simple_rerank(query, documents, top_k)
            
            # Note: OpenRouter has separate quota (200 requests/day) so no quota check needed
            
            # Format documents for LLM
            doc_list = []
            for i, doc in enumerate(documents):
                doc_str = f"""Document {i+1}:
- ID: {doc.get('id')}
- Title: {doc.get('title', 'Unknown')}
- Department: {doc.get('department', 'Unknown')}
- Type: {doc.get('document_type', 'Unknown')}
- Summary: {doc.get('summary', 'No summary')}
- Keywords: {', '.join(doc.get('keywords', [])[:10])}
"""
                doc_list.append(doc_str)
            
            docs_text = "\n".join(doc_list)
            
            # Get available document IDs for the prompt
            available_ids = [doc['id'] for doc in documents]
            
            prompt = f"""You are a document relevance expert. Given a user query and a list of documents, rank the documents by relevance.

User Query: "{query}"

Documents:
{docs_text}

IMPORTANT: Return ONLY a JSON array of the EXACT document IDs shown above (from the "ID:" field), in order of relevance (most relevant first).

Available document IDs: {available_ids}

Return up to {top_k} document IDs from the list above.
Format: [id1, id2, id3, ...]

Example: If available IDs are [17, 18, 19, 20, 21] and you want to rank them, return something like: [20, 18, 21, 17, 19]"""

            logger.info(f"Calling {self.provider} for reranking...")
            response = self.llm.invoke(prompt)
            
            # Consume quota after successful API call (only for Gemini)
            if self.provider == "gemini":
                try:
                    self.quota_manager.consume_quota("gemini_chat", 1)
                except Exception as e:
                    logger.error(f"Error consuming quota: {e}")
            
            # Parse response
            import json
            response_text = response.content.strip()
            logger.debug(f"{self.provider} response: {response_text}")
            
            # Extract JSON array
            if '[' in response_text and ']' in response_text:
                start = response_text.index('[')
                end = response_text.rindex(']') + 1
                ranked_ids = json.loads(response_text[start:end])
                
                logger.info(f"{self.provider} returned {len(ranked_ids)} document IDs: {ranked_ids}")
                
                # Reorder documents based on ranked IDs
                id_to_doc = {doc['id']: doc for doc in documents}
                logger.debug(f"Available document IDs: {list(id_to_doc.keys())}")
                
                reranked = []
                for doc_id in ranked_ids:
                    if doc_id in id_to_doc:
                        reranked.append(id_to_doc[doc_id])
                    else:
                        logger.warning(f"Document ID {doc_id} from {self.provider} not found in available documents")
                
                if not reranked:
                    logger.warning("No matching documents after reranking, falling back to original order")
                    logger.warning(f"{self.provider} returned IDs: {ranked_ids}, but available IDs are: {list(id_to_doc.keys())}")
                    return documents[:top_k]
                
                # If we got fewer documents than requested, add remaining from original list
                if len(reranked) < top_k:
                    reranked_ids = {doc['id'] for doc in reranked}
                    for doc in documents:
                        if doc['id'] not in reranked_ids and len(reranked) < top_k:
                            reranked.append(doc)
                
                logger.info(f"Reranked to top {len(reranked)} documents")
                return reranked[:top_k]
            
            else:
                logger.warning("Could not parse reranking response, using original order")
                return documents[:top_k]
            
        except Exception as e:
            logger.error(f"Error in {self.provider} reranking: {str(e)}")
            logger.info("Falling back to simple reranking due to error")
            return self._simple_rerank(query, documents, top_k)
    
    def _simple_rerank(self, query: str, documents: List[Dict], top_k: int) -> List[Dict]:
        """Simple keyword-based reranking (fallback)"""
        query_terms = set(query.lower().split())
        
        # Score documents based on keyword overlap
        scored_docs = []
        for doc in documents:
            score = 0
            
            # Check title
            if doc.get('title'):
                title_terms = set(doc['title'].lower().split())
                score += len(query_terms & title_terms) * 3
            
            # Check keywords
            if doc.get('keywords'):
                keyword_terms = set(' '.join(doc['keywords']).lower().split())
                score += len(query_terms & keyword_terms) * 2
            
            # Check summary
            if doc.get('summary'):
                summary_terms = set(doc['summary'].lower().split())
                score += len(query_terms & summary_terms)
            
            scored_docs.append((score, doc))
        
        # Sort by score
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        reranked = [doc for score, doc in scored_docs[:top_k]]
        
        logger.info(f"Simple reranking completed: {len(reranked)} documents")
        return reranked
