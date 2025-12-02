"""Analysis tools for comparing and summarizing documents"""
import logging
from typing import List
from pathlib import Path
import os
import numpy as np

from Agent.retrieval.hybrid_retriever import HybridRetriever
from Agent.embeddings.bge_embedder import BGEEmbedder
from Agent.vector_store.pgvector_store import PGVectorStore
from backend.database import SessionLocal, Document, DocumentMetadata, DocumentEmbedding

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
pgvector_store = PGVectorStore()


def compare_policies(document_ids: List[int], aspect: str) -> str:
    """
    Compare multiple documents on a specific aspect using pgvector.
    
    Args:
        document_ids: List of document IDs to compare
        aspect: The aspect to compare (e.g., "eligibility criteria", "funding")
    
    Returns:
        Comparison results with citations
    """
    logger.info(f"compare_policies called for docs {document_ids} on aspect: '{aspect}'")
    
    db = SessionLocal()
    try:
        if len(document_ids) < 2:
            return "Please provide at least 2 documents to compare."
        
        # Generate query embedding
        query_embedding = embedder.embed_text(aspect)
        if isinstance(query_embedding, list):
            query_embedding = np.array(query_embedding)
        
        comparison_results = {}
        
        for doc_id in document_ids:
            # Check if document exists
            doc = db.query(Document).filter(Document.id == doc_id).first()
            if not doc:
                comparison_results[doc_id] = "Document not found"
                continue
            
            # Check if document has embeddings
            embedding_count = db.query(DocumentEmbedding).filter(
                DocumentEmbedding.document_id == doc_id
            ).count()
            
            if embedding_count == 0:
                comparison_results[doc_id] = "Document not embedded yet"
                continue
            
            # Search for the aspect in this document
            results = db.query(DocumentEmbedding).filter(
                DocumentEmbedding.document_id == doc_id
            ).order_by(
                DocumentEmbedding.embedding.cosine_distance(query_embedding.tolist())
            ).limit(3).all()
            
            if results:
                # Calculate relevance score
                distance = np.linalg.norm(query_embedding - np.array(results[0].embedding))
                score = 1.0 / (1.0 + distance)
                
                comparison_results[doc_id] = {
                    "filename": doc.filename,
                    "relevant_text": results[0].chunk_text[:400],
                    "confidence": score,
                    "approval_status": doc.approval_status
                }
            else:
                comparison_results[doc_id] = "No relevant information found"
        
        # Format comparison
        formatted = f"**Comparison of '{aspect}' across {len(document_ids)} documents:**\n\n"
        
        for doc_id, result in comparison_results.items():
            if isinstance(result, dict):
                approval_badge = "✅" if result['approval_status'] == 'approved' else "⏳"
                formatted += f"**Document {doc_id}** {approval_badge} ({result['filename']})\n"
                formatted += f"Confidence: {result['confidence']:.2%}\n"
                formatted += f"Content: {result['relevant_text']}...\n\n"
            else:
                formatted += f"**Document {doc_id}**: {result}\n\n"
        
        db.close()
        logger.info(f"Comparison completed for {len(document_ids)} documents")
        return formatted
        
    except Exception as e:
        db.close()
        logger.error(f"Error in compare_policies: {str(e)}")
        return f"Error comparing policies: {str(e)}"


def summarize_document(document_id: int, focus: str = "general") -> str:
    """
    Generate a summary of a document using pgvector.
    
    Args:
        document_id: The document ID to summarize
        focus: Focus area for summary (e.g., "general", "key points", "requirements")
    
    Returns:
        Document summary with key chunks
    """
    logger.info(f"summarize_document called for doc {document_id}, focus: '{focus}'")
    
    db = SessionLocal()
    try:
        # Check if document exists
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            db.close()
            return f"Document {document_id} not found."
        
        # Check if document has embeddings
        embedding_count = db.query(DocumentEmbedding).filter(
            DocumentEmbedding.document_id == document_id
        ).count()
        
        if embedding_count == 0:
            db.close()
            return f"Document {document_id} has not been embedded yet. Please search for it first to trigger embedding."
        
        # Get document metadata
        metadata = db.query(DocumentMetadata).filter(
            DocumentMetadata.document_id == document_id
        ).first()
        
        filename = doc.filename
        doc_title = metadata.title if metadata else filename
        
        # Generate query embedding for focused summary
        query = f"main points {focus} overview summary key information"
        query_embedding = embedder.embed_text(query)
        if isinstance(query_embedding, list):
            query_embedding = np.array(query_embedding)
        
        # Search for most relevant chunks
        results = db.query(DocumentEmbedding).filter(
            DocumentEmbedding.document_id == document_id
        ).order_by(
            DocumentEmbedding.embedding.cosine_distance(query_embedding.tolist())
        ).limit(5).all()
        
        if not results:
            db.close()
            return f"Could not generate summary for document {document_id}."
        
        # Format summary
        formatted = f"**Summary of Document {document_id}**\n"
        formatted += f"Title: {doc_title}\n"
        formatted += f"Filename: {filename}\n"
        formatted += f"Total chunks: {embedding_count}\n"
        formatted += f"Focus: {focus}\n"
        formatted += f"Approval Status: {doc.approval_status}\n\n"
        formatted += "**Key sections:**\n\n"
        
        for i, result in enumerate(results, 1):
            # Calculate relevance score
            distance = np.linalg.norm(query_embedding - np.array(result.embedding))
            score = 1.0 / (1.0 + distance)
            
            formatted += f"{i}. Chunk {result.chunk_index} (Relevance: {score:.2%})\n"
            formatted += f"   {result.chunk_text[:300]}...\n\n"
        
        db.close()
        logger.info(f"Summary generated for doc {document_id}")
        return formatted
        
    except Exception as e:
        db.close()
        logger.error(f"Error in summarize_document: {str(e)}")
        return f"Error summarizing document: {str(e)}"
