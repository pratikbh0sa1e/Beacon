"""Search tools for RAG agent - pgvector version"""
import logging
from typing import Optional
from pathlib import Path

from backend.database import SessionLocal, Document, DocumentEmbedding

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


def get_document_metadata(document_id: Optional[int] = None) -> str:
    """
    Get metadata about documents in the system using pgvector.
    
    Args:
        document_id: Optional specific document ID. If None, returns all documents.
    
    Returns:
        Formatted document metadata
    """
    logger.info(f"get_document_metadata called for doc: {document_id}")
    
    try:
        db = SessionLocal()
        
        if document_id:
            # Get specific document info
            document = db.query(Document).filter(Document.id == document_id).first()
            
            if not document:
                return f"Document {document_id} not found."
            
            # Get embedding count
            embedding_count = db.query(DocumentEmbedding).filter(
                DocumentEmbedding.document_id == document_id
            ).count()
            
            return f"""Document {document_id} Metadata:
- Filename: {document.filename}
- Total chunks: {embedding_count}
- Embedding dimension: 1024
- Storage: pgvector (PostgreSQL)
- Approval Status: {document.approval_status}
- Visibility: {document.visibility_level}
"""
        else:
            # Get all documents
            documents = db.query(Document).all()
            
            if not documents:
                return "No documents in the system."
            
            formatted = f"Total documents: {len(documents)}\n\n"
            for doc in documents:
                embedding_count = db.query(DocumentEmbedding).filter(
                    DocumentEmbedding.document_id == doc.id
                ).count()
                
                formatted += f"Document {doc.id} ({doc.filename}): {embedding_count} chunks - Status: {doc.approval_status}\n"
            
            return formatted
            
    except Exception as e:
        logger.error(f"Error in get_document_metadata: {str(e)}")
        return f"Error getting metadata: {str(e)}"
    finally:
        db.close()
