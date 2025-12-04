import hashlib
from typing import Dict, List
import logging
from pathlib import Path
from Agent.chunking.adaptive_chunker import AdaptiveChunker
from Agent.embeddings.bge_embedder import BGEEmbedder
from Agent.vector_store.pgvector_store import PGVectorStore

# Setup logging
log_dir = Path("Agent/agent_logs")
log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "pipeline.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EmbeddingPipeline:
    """Complete pipeline for document embedding"""
    
    def __init__(self, chunker=None, embedder=None, vector_store=None, use_separate_indexes=False):
        self.chunker = chunker or AdaptiveChunker()
        self.embedder = embedder or BGEEmbedder()
        self.vector_store = vector_store or PGVectorStore()  # Use pgvector by default
        self.use_separate_indexes = use_separate_indexes  # Deprecated, kept for compatibility
    
    def _generate_doc_hash(self, text: str, filename: str) -> str:
        """Generate unique hash for document"""
        content = f"{filename}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def process_document(self, text: str, metadata: Dict) -> Dict:
        """
        Process a document: chunk, embed, and store
        
        Args:
            text: Document text
            metadata: Document metadata (document_id, filename, file_type, source_department)
            
        Returns:
            Dict with processing results
        """
        filename = metadata.get("filename", "unknown")
        document_id = metadata.get("document_id", "unknown")
        logger.info(f"Processing document: {filename}")
        
        # Generate document hash
        doc_hash = self._generate_doc_hash(text, filename)
        logger.debug(f"Document hash: {doc_hash}")
        
        # Use pgvector (centralized storage)
        vector_store = self.vector_store
        logger.info(f"Using pgvector for document {document_id}")
        
        # Note: Duplicate detection handled at database level
        # pgvector will replace existing embeddings for the same document_id
        
        # Chunk the text
        logger.info(f"Chunking text (length: {len(text)} chars)")
        chunks = self.chunker.chunk_text(text, metadata)
        
        if not chunks:
            logger.error("No chunks generated from text")
            return {
                "status": "error",
                "message": "No chunks generated from text"
            }
        
        logger.info(f"Generated {len(chunks)} chunks")
        
        # Extract chunk texts
        chunk_texts = [chunk["text"] for chunk in chunks]
        chunk_metadata = [chunk["metadata"] for chunk in chunks]
        
        # Generate embeddings
        logger.info("Generating embeddings...")
        embeddings = self.embedder.embed_batch(chunk_texts)
        
        # Store in pgvector database
        logger.info("Storing embeddings in pgvector...")
        # Note: This should be called from the document upload endpoint with proper DB session
        # The actual storage is handled by pgvector_store.add_embeddings()
        
        logger.info(f"Successfully processed {filename}: {len(chunks)} chunks, {len(embeddings)} embeddings")
        
        return {
            "status": "success",
            "doc_hash": doc_hash,
            "num_chunks": len(chunks),
            "num_embeddings": len(embeddings),
            "embeddings": embeddings,
            "chunk_metadata": chunk_metadata,
            "storage": "pgvector"
        }
