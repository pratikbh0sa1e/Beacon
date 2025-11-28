"""Document reranker for Lazy RAG - modular design"""
import logging
from typing import List, Dict
from pathlib import Path
from langchain_google_genai import ChatGoogleGenerativeAI
import os

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
    """Rerank documents based on query relevance"""
    
    def __init__(self, provider: str = "gemini", google_api_key: str = None):
        """
        Initialize reranker
        
        Args:
            provider: "gemini" or "local" (for future local model support)
            google_api_key: Google API key (required for gemini provider)
        """
        self.provider = provider
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        
        if provider == "gemini":
            if not self.google_api_key:
                raise ValueError("Google API key required for Gemini reranker")
            
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=self.google_api_key,
                temperature=0.1
            )
            logger.info("Reranker initialized with Gemini")
        
        elif provider == "local":
            # Placeholder for future local model implementation
            logger.warning("Local reranker not yet implemented - falling back to simple scoring")
            self.llm = None
        
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
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
        
        if self.provider == "gemini":
            return self._gemini_rerank(query, documents, top_k)
        elif self.provider == "local":
            return self._simple_rerank(query, documents, top_k)
        else:
            return documents[:top_k]
    
    def _gemini_rerank(self, query: str, documents: List[Dict], top_k: int) -> List[Dict]:
        """Rerank using Gemini LLM"""
        try:
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

            logger.info("Calling Gemini for reranking...")
            response = self.llm.invoke(prompt)
            
            # Parse response
            import json
            response_text = response.content.strip()
            logger.debug(f"Gemini response: {response_text}")
            
            # Extract JSON array
            if '[' in response_text and ']' in response_text:
                start = response_text.index('[')
                end = response_text.rindex(']') + 1
                ranked_ids = json.loads(response_text[start:end])
                
                logger.info(f"Gemini returned {len(ranked_ids)} document IDs: {ranked_ids}")
                
                # Reorder documents based on ranked IDs
                id_to_doc = {doc['id']: doc for doc in documents}
                logger.debug(f"Available document IDs: {list(id_to_doc.keys())}")
                
                reranked = []
                for doc_id in ranked_ids:
                    if doc_id in id_to_doc:
                        reranked.append(id_to_doc[doc_id])
                    else:
                        logger.warning(f"Document ID {doc_id} from Gemini not found in available documents")
                
                if not reranked:
                    logger.warning("No matching documents after reranking, falling back to original order")
                    logger.warning(f"Gemini returned IDs: {ranked_ids}, but available IDs are: {list(id_to_doc.keys())}")
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
            logger.error(f"Error in Gemini reranking: {str(e)}")
            return documents[:top_k]
    
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
