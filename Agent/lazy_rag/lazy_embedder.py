"""Lazy embedding service - embed documents on-demand using pgvector"""
import logging
from typing import List, Dict
from pathlib import Path
import os
import httpx

from Agent.embeddings.bge_embedder import BGEEmbedder
from Agent.chunking.adaptive_chunker import AdaptiveChunker
from Agent.vector_store.pgvector_store import PGVectorStore
from backend.database import SessionLocal, Document, DocumentMetadata

# Setup logging
log_dir = Path("Agent/agent_logs")
log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "lazy_rag.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class LazyEmbedder:
    """Embed documents on-demand for Lazy RAG"""
    
    def __init__(self):
        """Initialize lazy embedder with pgvector"""
        self.embedder = BGEEmbedder()
        self.chunker = AdaptiveChunker()
        self.pgvector_store = PGVectorStore()
        logger.info("Lazy embedder initialized with pgvector")
    
    def embed_document(self, doc_id: int, text: str = None, filename: str = None) -> Dict:
        """
        Embed a single document on-demand using pgvector
        
        Args:
            doc_id: Document ID
            text: Full document text (optional, will fetch from DB if not provided)
            filename: Original filename (optional, will fetch from DB if not provided)
        
        Returns:
            Dictionary with embedding results
        """
        logger.info(f"Lazy embedding document {doc_id}")
        db = SessionLocal()
        
        try:
            # Get document from database
            doc = db.query(Document).filter(Document.id == doc_id).first()
            if not doc:
                return {
                    "status": "error",
                    "message": f"Document {doc_id} not found",
                    "doc_id": doc_id
                }
            
            # Use provided text or fetch from document
            if text is None:
                # Try to get text from S3 if available
                if doc.s3_url:
                    logger.info(f"Fetching document from S3: {doc.s3_url}")
                    text = self._fetch_text_from_s3(doc.s3_url, doc.file_type)
                else:
                    text = doc.extracted_text
            
            if filename is None:
                filename = doc.filename
            
            if not text:
                return {
                    "status": "error",
                    "message": "No text available for embedding",
                    "doc_id": doc_id
                }
            
            # Chunk the text
            logger.info(f"Chunking text (length: {len(text)} chars)")
            chunk_dicts = self.chunker.chunk_text(text)
            logger.info(f"Generated {len(chunk_dicts)} chunks")
            
            if not chunk_dicts:
                logger.warning(f"No chunks generated for document {doc_id}")
                return {
                    "status": "error",
                    "message": "No chunks generated",
                    "num_chunks": 0,
                    "doc_id": doc_id
                }
            
            # Extract just the text strings for embedding
            chunks = [chunk_dict["text"] for chunk_dict in chunk_dicts]
            
            # Generate embeddings
            logger.info("Generating embeddings...")
            embeddings = self.embedder.embed_batch(chunks)
            
            # Create metadata for each chunk
            metadata_list = []
            for i, chunk_text in enumerate(chunks):
                metadata_list.append({
                    "chunk_index": i,
                    "filename": filename,
                    "document_id": doc_id,
                    "text_length": len(chunk_text)
                })
            
            # Store in pgvector
            logger.info(f"Storing {len(embeddings)} embeddings in pgvector...")
            num_added = self.pgvector_store.add_embeddings(
                document_id=doc_id,
                chunks=chunks,
                embeddings=embeddings,
                metadata_list=metadata_list,
                visibility_level=doc.visibility_level,
                institution_id=doc.institution_id,
                approval_status=doc.approval_status,
                db=db
            )
            
            # Update embedding status in metadata
            metadata = db.query(DocumentMetadata).filter(
                DocumentMetadata.document_id == doc_id
            ).first()
            if metadata:
                metadata.embedding_status = 'embedded'
                db.commit()
            
            logger.info(f"Successfully embedded document {doc_id}: {len(chunk_dicts)} chunks")
            
            return {
                "status": "success",
                "doc_id": doc_id,
                "num_chunks": len(chunk_dicts),
                "num_embeddings": num_added
            }
            
        except Exception as e:
            logger.error(f"Error embedding document {doc_id}: {str(e)}")
            db.rollback()
            return {
                "status": "error",
                "message": str(e),
                "doc_id": doc_id
            }
        finally:
            db.close()
    
    def _fetch_text_from_s3(self, s3_url: str, file_type: str) -> str:
        """
        Fetch document from S3 and extract text
        
        Args:
            s3_url: S3 URL of the document
            file_type: File type (pdf, docx, etc.)
        
        Returns:
            Extracted text
        """
        import tempfile
        from backend.utils.text_extractor import extract_text
        
        try:
            # Download file from S3
            response = httpx.get(s3_url, timeout=30.0)
            response.raise_for_status()
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type}") as tmp_file:
                tmp_file.write(response.content)
                tmp_path = tmp_file.name
            
            # Extract text
            text = extract_text(tmp_path, file_type)
            
            # Clean up
            os.unlink(tmp_path)
            
            return text
            
        except Exception as e:
            logger.error(f"Error fetching from S3: {str(e)}")
            raise
    
    def embed_documents_batch(self, documents: List[Dict]) -> List[Dict]:
        """
        Embed multiple documents (for batch processing)
        
        Args:
            documents: List of dicts with {id, text, filename}
        
        Returns:
            List of embedding results
        """
        logger.info(f"Batch embedding {len(documents)} documents")
        
        results = []
        for doc in documents:
            result = self.embed_document(
                doc_id=doc['id'],
                text=doc['text'],
                filename=doc['filename']
            )
            results.append(result)
        
        successful = sum(1 for r in results if r['status'] == 'success')
        logger.info(f"Batch embedding complete: {successful}/{len(documents)} successful")
        
        return results
    
    def check_embedding_status(self, doc_id: int) -> str:
        """
        Check if document is already embedded in pgvector
        
        Args:
            doc_id: Document ID
        
        Returns:
            Status: 'embedded', 'not_embedded', or 'error'
        """
        db = SessionLocal()
        try:
            from backend.database import DocumentEmbedding
            count = db.query(DocumentEmbedding).filter(
                DocumentEmbedding.document_id == doc_id
            ).count()
            
            return 'embedded' if count > 0 else 'not_embedded'
        except Exception as e:
            logger.error(f"Error checking embedding status: {str(e)}")
            return 'error'
        finally:
            db.close()
