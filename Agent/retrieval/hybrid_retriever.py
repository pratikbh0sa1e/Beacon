import numpy as np
from typing import List, Dict, Tuple
from rank_bm25 import BM25Okapi
import logging
from pathlib import Path

# Setup logging
log_dir = Path("Agent/agent_logs")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "retrieval.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HybridRetriever:
    """Hybrid retriever combining vector search (semantic) and BM25 (keyword)"""
    
    def __init__(self, vector_weight: float = 0.7, bm25_weight: float = 0.3):
        """
        Initialize hybrid retriever
        
        Args:
            vector_weight: Weight for vector similarity scores (0-1)
            bm25_weight: Weight for BM25 scores (0-1)
        """
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        logger.info(f"Initialized HybridRetriever (vector: {vector_weight}, bm25: {bm25_weight})")
    
    def _normalize_scores(self, scores: List[float]) -> List[float]:
        """Normalize scores to 0-1 range"""
        if not scores or max(scores) == min(scores):
            return [0.0] * len(scores)
        min_score = min(scores)
        max_score = max(scores)
        return [(s - min_score) / (max_score - min_score) for s in scores]
    
    def retrieve(
        self,
        query: str,
        vector_store,
        embedder,
        top_k: int = 5,
        min_score: float = 0.3
    ) -> List[Dict]:
        """
        Hybrid retrieval combining vector and BM25 search
        
        Args:
            query: Search query
            vector_store: FAISS vector store
            embedder: Embedding model
            top_k: Number of results to return
            min_score: Minimum combined score threshold
            
        Returns:
            List of retrieved chunks with metadata and scores
        """
        logger.info(f"Hybrid search for query: '{query[:50]}...'")
        
        # 1. Vector search (semantic)
        query_embedding = embedder.embed_text(query)
        vector_results = vector_store.search(query_embedding, k=top_k * 2)
        
        if not vector_results:
            logger.warning("No vector results found")
            return []
        
        # Debug: Log first result structure
        if vector_results:
            logger.debug(f"First result structure: {list(vector_results[0].keys())}")
            logger.debug(f"First metadata keys: {list(vector_results[0].get('metadata', {}).keys())}")
        
        # Extract texts and metadata
        texts = []
        metadata_list = []
        vector_scores = []
        
        for result in vector_results:
            metadata = result.get("metadata", {})
            chunk_text = metadata.get("chunk_text", "")
            
            # Handle case where chunk_text might be a dict (shouldn't happen but defensive)
            if isinstance(chunk_text, dict):
                logger.warning(f"chunk_text is a dict: {chunk_text}")
                chunk_text = str(chunk_text)
            
            if chunk_text and isinstance(chunk_text, str):
                texts.append(chunk_text)
                metadata_list.append(metadata)
                # Convert L2 distance to similarity (lower is better, so invert)
                vector_scores.append(1 / (1 + result.get("distance", 1)))
        
        if not texts:
            logger.warning("No valid texts in vector results")
            return []
        
        # 2. BM25 search (keyword)
        try:
            tokenized_corpus = [text.lower().split() for text in texts]
            bm25 = BM25Okapi(tokenized_corpus)
            tokenized_query = query.lower().split()
            bm25_scores = bm25.get_scores(tokenized_query)
        except AttributeError as e:
            logger.error(f"Error tokenizing texts: {e}")
            logger.error(f"Texts type check: {[type(t) for t in texts[:3]]}")
            raise
        
        # 3. Normalize scores
        norm_vector_scores = self._normalize_scores(vector_scores)
        norm_bm25_scores = self._normalize_scores(bm25_scores.tolist())
        
        # 4. Combine scores
        combined_results = []
        for i, (text, metadata) in enumerate(zip(texts, metadata_list)):
            combined_score = (
                self.vector_weight * norm_vector_scores[i] +
                self.bm25_weight * norm_bm25_scores[i]
            )
            
            if combined_score >= min_score:
                combined_results.append({
                    "text": text,
                    "metadata": metadata,
                    "score": combined_score,
                    "vector_score": norm_vector_scores[i],
                    "bm25_score": norm_bm25_scores[i]
                })
        
        # 5. Sort by combined score and return top_k
        combined_results.sort(key=lambda x: x["score"], reverse=True)
        final_results = combined_results[:top_k]
        
        logger.info(f"Retrieved {len(final_results)} results (min_score: {min_score})")
        return final_results
