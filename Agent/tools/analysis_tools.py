"""Analysis tools for comparing and summarizing documents"""
import logging
from typing import List
from pathlib import Path
import os

from Agent.retrieval.hybrid_retriever import HybridRetriever
from Agent.embeddings.bge_embedder import BGEEmbedder
from Agent.vector_store.faiss_store import FAISSVectorStore

# Setup logging
log_dir = Path("Agent/agent_logs")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "tools.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

embedder = BGEEmbedder()
retriever = HybridRetriever()


def compare_policies(document_ids: List[int], aspect: str) -> str:
    """
    Compare multiple documents on a specific aspect.
    
    Args:
        document_ids: List of document IDs to compare
        aspect: The aspect to compare (e.g., "eligibility criteria", "funding")
    
    Returns:
        Comparison results with citations
    """
    logger.info(f"compare_policies called for docs {document_ids} on aspect: '{aspect}'")
    
    try:
        if len(document_ids) < 2:
            return "Please provide at least 2 documents to compare."
        
        comparison_results = {}
        
        for doc_id in document_ids:
            index_path = f"Agent/vector_store/documents/{doc_id}/faiss_index"
            
            if not os.path.exists(f"{index_path}.index"):
                comparison_results[doc_id] = "Document not found"
                continue
            
            # Load vector store
            vector_store = FAISSVectorStore(index_path=index_path)
            
            # Search for the aspect
            results = retriever.retrieve(aspect, vector_store, embedder, top_k=3)
            
            if results:
                comparison_results[doc_id] = {
                    "filename": results[0]["metadata"].get("filename", "Unknown"),
                    "relevant_text": results[0]["text"][:400],
                    "confidence": results[0]["score"]
                }
            else:
                comparison_results[doc_id] = "No relevant information found"
        
        # Format comparison
        formatted = f"Comparison of '{aspect}' across {len(document_ids)} documents:\n\n"
        
        for doc_id, result in comparison_results.items():
            if isinstance(result, dict):
                formatted += f"**Document {doc_id}** ({result['filename']})\n"
                formatted += f"Confidence: {result['confidence']:.2%}\n"
                formatted += f"Content: {result['relevant_text']}...\n\n"
            else:
                formatted += f"**Document {doc_id}**: {result}\n\n"
        
        logger.info(f"Comparison completed for {len(document_ids)} documents")
        return formatted
        
    except Exception as e:
        logger.error(f"Error in compare_policies: {str(e)}")
        return f"Error comparing policies: {str(e)}"


def summarize_document(document_id: int, focus: str = "general") -> str:
    """
    Generate a summary of a document.
    
    Args:
        document_id: The document ID to summarize
        focus: Focus area for summary (e.g., "general", "key points", "requirements")
    
    Returns:
        Document summary with key chunks
    """
    logger.info(f"summarize_document called for doc {document_id}, focus: '{focus}'")
    
    try:
        index_path = f"Agent/vector_store/documents/{document_id}/faiss_index"
        
        if not os.path.exists(f"{index_path}.index"):
            return f"Document {document_id} not found."
        
        # Load vector store
        vector_store = FAISSVectorStore(index_path=index_path)
        stats = vector_store.get_stats()
        
        # Get representative chunks based on focus
        query = f"main points {focus} overview summary"
        results = retriever.retrieve(query, vector_store, embedder, top_k=5)
        
        if not results:
            return f"Could not generate summary for document {document_id}."
        
        # Format summary
        filename = results[0]["metadata"].get("filename", "Unknown")
        formatted = f"Summary of Document {document_id} ({filename}):\n"
        formatted += f"Total chunks: {stats['total_vectors']}\n"
        formatted += f"Focus: {focus}\n\n"
        formatted += "Key sections:\n\n"
        
        for i, result in enumerate(results, 1):
            formatted += f"{i}. (Chunk {result['metadata'].get('chunk_index', 'N/A')})\n"
            formatted += f"   {result['text'][:250]}...\n\n"
        
        logger.info(f"Summary generated for doc {document_id}")
        return formatted
        
    except Exception as e:
        logger.error(f"Error in summarize_document: {str(e)}")
        return f"Error summarizing document: {str(e)}"
