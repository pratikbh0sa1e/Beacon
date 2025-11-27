import hashlib
from typing import Dict, List
import logging
from pathlib import Path
from Agent.chunking.adaptive_chunker import AdaptiveChunker
from Agent.embeddings.bge_embedder import BGEEmbedder
from Agent.vector_store.faiss_store import FAISSVectorStore

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
    
    def __init__(self, chunker=None, embedder=None, vector_store=None):
        self.chunker = chunker or AdaptiveChunker()
        self.embedder = embedder or BGEEmbedder()
        self.vector_store = vector_store or FAISSVectorStore()
    
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
        logger.info(f"Processing document: {filename}")
        
        # Generate document hash
        doc_hash = self._generate_doc_hash(text, filename)
        logger.debug(f"Document hash: {doc_hash}")
        
        # Check if document already exists
        if self.vector_store.document_exists(doc_hash):
            logger.info(f"Document {filename} already exists, skipping")
            return {
                "status": "skipped",
                "message": "Document already exists in vector store",
                "doc_hash": doc_hash
            }
        
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
        
        # Store in vector database
        logger.info("Storing embeddings in FAISS...")
        success = self.vector_store.add_embeddings(embeddings, chunk_metadata, doc_hash)
        
        if success:
            logger.info(f"Successfully processed {filename}: {len(chunks)} chunks, {len(embeddings)} embeddings")
        else:
            logger.error(f"Failed to store embeddings for {filename}")
        
        return {
            "status": "success" if success else "error",
            "doc_hash": doc_hash,
            "num_chunks": len(chunks),
            "num_embeddings": len(embeddings)
        }
