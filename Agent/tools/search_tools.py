"""Search tools for RAG agent"""
import logging
from typing import List, Dict, Optional
from pathlib import Path
import glob
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

# Initialize shared components
embedder = BGEEmbedder()
retriever = HybridRetriever(vector_weight=0.7, bm25_weight=0.3)


def search_documents(query: str, top_k: int = 5) -> str:
    """
    Search across all documents using hybrid retrieval (vector + BM25).
    
    Args:
        query: The search query
        top_k: Number of results to return (default: 5)
    
    Returns:
        Formatted search results with citations
    """
    logger.info(f"search_documents called with query: '{query}'")
    
    try:
        # Get all document folders
        doc_folders = glob.glob("Agent/vector_store/documents/*/")
        
        if not doc_folders:
            return "No documents found in the system."
        
        all_results = []
        
        # Search across all documents
        for doc_folder in doc_folders:
            doc_id = os.path.basename(os.path.dirname(doc_folder))
            index_path = f"{doc_folder}faiss_index"
            
            if not os.path.exists(f"{index_path}.index"):
                continue
            
            # Load vector store for this document
            vector_store = FAISSVectorStore(index_path=index_path)
            
            # Perform hybrid search
            results = retriever.retrieve(query, vector_store, embedder, top_k=top_k)
            
            # Add document ID to results
            for result in results:
                result["document_id"] = doc_id
                all_results.append(result)
        
        if not all_results:
            return "No relevant information found."
        
        # Sort by score and take top_k
        all_results.sort(key=lambda x: x["score"], reverse=True)
        top_results = all_results[:top_k]
        
        # Format results
        formatted = f"Found {len(top_results)} relevant results:\n\n"
        for i, result in enumerate(top_results, 1):
            metadata = result["metadata"]
            formatted += f"**Result {i}** (Confidence: {result['score']:.2%})\n"
            formatted += f"Source: {metadata.get('filename', 'Unknown')}\n"
            formatted += f"Document ID: {result['document_id']}\n"
            formatted += f"Chunk: {metadata.get('chunk_index', 'N/A')}\n"
            formatted += f"Text: {result['text'][:300]}...\n\n"
        
        logger.info(f"Returned {len(top_results)} results")
        return formatted
        
    except Exception as e:
        logger.error(f"Error in search_documents: {str(e)}")
        return f"Error searching documents: {str(e)}"


def search_specific_document(document_id: int, query: str, top_k: int = 5) -> str:
    """
    Search within a specific document.
    
    Args:
        document_id: The document ID to search in
        query: The search query
        top_k: Number of results to return
    
    Returns:
        Formatted search results from the specific document
    """
    logger.info(f"search_specific_document called for doc {document_id}: '{query}'")
    
    try:
        index_path = f"Agent/vector_store/documents/{document_id}/faiss_index"
        
        if not os.path.exists(f"{index_path}.index"):
            return f"Document {document_id} not found or not indexed."
        
        # Load vector store
        vector_store = FAISSVectorStore(index_path=index_path)
        
        # Perform hybrid search
        results = retriever.retrieve(query, vector_store, embedder, top_k=top_k)
        
        if not results:
            return f"No relevant information found in document {document_id}."
        
        # Format results
        formatted = f"Found {len(results)} results in Document {document_id}:\n\n"
        for i, result in enumerate(results, 1):
            metadata = result["metadata"]
            formatted += f"**Result {i}** (Confidence: {result['score']:.2%})\n"
            formatted += f"Source: {metadata.get('filename', 'Unknown')}\n"
            formatted += f"Chunk: {metadata.get('chunk_index', 'N/A')}\n"
            formatted += f"Text: {result['text'][:300]}...\n\n"
        
        logger.info(f"Returned {len(results)} results from doc {document_id}")
        return formatted
        
    except Exception as e:
        logger.error(f"Error in search_specific_document: {str(e)}")
        return f"Error searching document: {str(e)}"


def get_document_metadata(document_id: Optional[int] = None) -> str:
    """
    Get metadata about documents in the system.
    
    Args:
        document_id: Optional specific document ID. If None, returns all documents.
    
    Returns:
        Formatted document metadata
    """
    logger.info(f"get_document_metadata called for doc: {document_id}")
    
    try:
        if document_id:
            # Get specific document info
            index_path = f"Agent/vector_store/documents/{document_id}/faiss_index"
            
            if not os.path.exists(f"{index_path}.index"):
                return f"Document {document_id} not found."
            
            vector_store = FAISSVectorStore(index_path=index_path)
            stats = vector_store.get_stats()
            
            return f"""Document {document_id} Metadata:
- Total chunks: {stats['total_vectors']}
- Embedding dimension: {stats['dimension']}
- Storage path: {index_path}
"""
        else:
            # Get all documents
            doc_folders = glob.glob("Agent/vector_store/documents/*/")
            
            if not doc_folders:
                return "No documents in the system."
            
            formatted = f"Total documents: {len(doc_folders)}\n\n"
            for doc_folder in doc_folders:
                doc_id = os.path.basename(os.path.dirname(doc_folder))
                index_path = f"{doc_folder}faiss_index"
                
                if os.path.exists(f"{index_path}.index"):
                    vector_store = FAISSVectorStore(index_path=index_path)
                    stats = vector_store.get_stats()
                    formatted += f"Document {doc_id}: {stats['total_vectors']} chunks\n"
            
            return formatted
            
    except Exception as e:
        logger.error(f"Error in get_document_metadata: {str(e)}")
        return f"Error getting metadata: {str(e)}"
