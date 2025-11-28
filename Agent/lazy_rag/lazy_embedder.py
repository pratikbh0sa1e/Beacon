"""Lazy embedding service - embed documents on-demand"""
import logging
from typing import List, Dict
from pathlib import Path
import os

from Agent.embeddings.bge_embedder import BGEEmbedder
from Agent.chunking.adaptive_chunker import AdaptiveChunker
from Agent.vector_store.faiss_store import FAISSVectorStore

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
        """Initialize lazy embedder"""
        self.embedder = BGEEmbedder()
        self.chunker = AdaptiveChunker()
        logger.info("Lazy embedder initialized")
    
    def embed_document(self, doc_id: int, text: str, filename: str) -> Dict:
        """
        Embed a single document on-demand
        
        Args:
            doc_id: Document ID
            text: Full document text
            filename: Original filename
        
        Returns:
            Dictionary with embedding results
        """
        logger.info(f"Lazy embedding document {doc_id}: {filename}")
        
        try:
            # Create document directory
            doc_dir = Path(f"Agent/vector_store/documents/{doc_id}")
            doc_dir.mkdir(parents=True, exist_ok=True)
            
            # Chunk the text
            logger.info(f"Chunking text (length: {len(text)} chars)")
            chunk_dicts = self.chunker.chunk_text(text)
            logger.info(f"Generated {len(chunk_dicts)} chunks")
            
            if not chunk_dicts:
                logger.warning(f"No chunks generated for document {doc_id}")
                return {
                    "status": "error",
                    "message": "No chunks generated",
                    "num_chunks": 0
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
                    "text_length": len(chunk_text),
                    "chunk_text": chunk_text  # Store the actual text string for retrieval
                })
            
            # Store in FAISS
            index_path = str(doc_dir / "faiss_index")
            vector_store = FAISSVectorStore(index_path=index_path)
            
            # Create document hash
            import hashlib
            doc_hash = hashlib.sha256(text.encode()).hexdigest()
            
            logger.info(f"Storing {len(embeddings)} embeddings in FAISS...")
            vector_store.add_embeddings(embeddings, metadata_list, doc_hash)
            
            logger.info(f"Successfully embedded document {doc_id}: {len(chunk_dicts)} chunks")
            
            return {
                "status": "success",
                "doc_id": doc_id,
                "num_chunks": len(chunk_dicts),
                "num_embeddings": len(embeddings),
                "index_path": index_path
            }
            
        except Exception as e:
            logger.error(f"Error embedding document {doc_id}: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "doc_id": doc_id
            }
    
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
        Check if document is already embedded
        
        Args:
            doc_id: Document ID
        
        Returns:
            Status: 'embedded', 'not_embedded', or 'error'
        """
        index_path = f"Agent/vector_store/documents/{doc_id}/faiss_index.index"
        
        if os.path.exists(index_path):
            return 'embedded'
        else:
            return 'not_embedded'
