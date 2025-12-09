"""
Parallel Document Embedding Script

Embeds all unembed documents in the database using Google Gemini embeddings
with 5 parallel workers and duplicate detection.

Features:
- Uses Google Gemini multilingual embeddings (768 dims, padded to 1024)
- Parallel processing with 5 workers
- Duplicate detection (skips already embedded documents)
- Stores embeddings in pgvector (document_embeddings table)
- Comprehensive logging and progress tracking

Usage:
    python embed_all_documents.py
    
Requirements:
    - GOOGLE_API_KEY in .env file
    - PostgreSQL with pgvector extension
    - Documents in database with metadata_status='ready'
"""

import os
import sys
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List, Dict, Set
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database import SessionLocal, Document, DocumentMetadata, DocumentEmbedding
from Agent.lazy_rag.lazy_embedder import LazyEmbedder

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('embed_all_documents.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
NUM_WORKERS = 5
BATCH_SIZE = 100  # Process in batches to avoid memory issues


class ParallelDocumentEmbedder:
    """Parallel document embedder with duplicate detection"""
    
    def __init__(self, num_workers: int = 5):
        """
        Initialize the parallel embedder
        
        Args:
            num_workers: Number of parallel workers
        """
        self.num_workers = num_workers
        self.lazy_embedder = LazyEmbedder()
        self.stats = {
            'total': 0,
            'embedded': 0,
            'skipped': 0,
            'failed': 0,
            'duplicates': 0
        }
    
    def get_unembed_documents(self) -> List[Dict]:
        """
        Get all documents that need embedding
        
        Returns:
            List of document dictionaries with id, filename, and status
        """
        logger.info("Fetching unembed documents from database...")
        
        db = SessionLocal()
        try:
            # Query documents that are not embedded yet
            query = db.query(Document, DocumentMetadata).join(
                DocumentMetadata, Document.id == DocumentMetadata.document_id
            ).filter(
                DocumentMetadata.embedding_status != 'embedded',
                DocumentMetadata.metadata_status == 'ready',  # Only embed if metadata is ready
                Document.approval_status.in_(['approved', 'pending'])
            )
            
            results = query.all()
            
            documents = []
            for doc, meta in results:
                documents.append({
                    'id': doc.id,
                    'filename': doc.filename,
                    'title': meta.title or doc.filename,
                    'embedding_status': meta.embedding_status,
                    'metadata_status': meta.metadata_status
                })
            
            logger.info(f"Found {len(documents)} documents to embed")
            return documents
            
        finally:
            db.close()
    
    def check_already_embedded(self, document_id: int) -> bool:
        """
        Check if document already has embeddings (duplicate detection)
        
        Args:
            document_id: Document ID to check
            
        Returns:
            True if document already has embeddings, False otherwise
        """
        db = SessionLocal()
        try:
            count = db.query(DocumentEmbedding).filter(
                DocumentEmbedding.document_id == document_id
            ).count()
            
            return count > 0
            
        finally:
            db.close()
    
    def embed_document(self, doc_info: Dict) -> Dict:
        """
        Embed a single document
        
        Args:
            doc_info: Document information dictionary
            
        Returns:
            Result dictionary with status and details
        """
        doc_id = doc_info['id']
        filename = doc_info['filename']
        
        try:
            # Check for duplicates first
            if self.check_already_embedded(doc_id):
                logger.warning(f"⚠️  Document {doc_id} ({filename}) already has embeddings - SKIPPING (duplicate)")
                return {
                    'doc_id': doc_id,
                    'filename': filename,
                    'status': 'duplicate',
                    'message': 'Already embedded'
                }
            
            # Embed the document
            logger.info(f"🔄 Embedding document {doc_id}: {filename}")
            result = self.lazy_embedder.embed_document(doc_id)
            
            if result['status'] == 'success':
                logger.info(f"✅ Successfully embedded document {doc_id}: {result['num_chunks']} chunks")
                return {
                    'doc_id': doc_id,
                    'filename': filename,
                    'status': 'success',
                    'num_chunks': result['num_chunks'],
                    'message': result.get('message', 'Success')
                }
            else:
                logger.error(f"❌ Failed to embed document {doc_id}: {result.get('message', 'Unknown error')}")
                return {
                    'doc_id': doc_id,
                    'filename': filename,
                    'status': 'failed',
                    'message': result.get('message', 'Unknown error')
                }
                
        except Exception as e:
            logger.error(f"❌ Error embedding document {doc_id}: {str(e)}")
            return {
                'doc_id': doc_id,
                'filename': filename,
                'status': 'error',
                'message': str(e)
            }
    
    def embed_all_parallel(self):
        """
        Embed all unembed documents in parallel
        """
        start_time = datetime.now()
        logger.info(f"🚀 Starting parallel embedding with {self.num_workers} workers")
        logger.info("=" * 80)
        
        # Get all documents to embed
        documents = self.get_unembed_documents()
        self.stats['total'] = len(documents)
        
        if not documents:
            logger.info("✨ No documents to embed!")
            return
        
        logger.info(f"📊 Total documents to process: {len(documents)}")
        logger.info("=" * 80)
        
        # Process documents in parallel
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            # Submit all tasks
            future_to_doc = {
                executor.submit(self.embed_document, doc): doc 
                for doc in documents
            }
            
            # Process completed tasks
            for i, future in enumerate(as_completed(future_to_doc), 1):
                doc = future_to_doc[future]
                
                try:
                    result = future.result()
                    
                    # Update statistics
                    if result['status'] == 'success':
                        self.stats['embedded'] += 1
                    elif result['status'] == 'duplicate':
                        self.stats['duplicates'] += 1
                        self.stats['skipped'] += 1
                    elif result['status'] in ['failed', 'error']:
                        self.stats['failed'] += 1
                    else:
                        self.stats['skipped'] += 1
                    
                    # Progress update
                    progress = (i / len(documents)) * 100
                    logger.info(f"📈 Progress: {i}/{len(documents)} ({progress:.1f}%) - "
                              f"✅ {self.stats['embedded']} | "
                              f"⚠️  {self.stats['duplicates']} duplicates | "
                              f"❌ {self.stats['failed']} failed")
                    
                except Exception as e:
                    logger.error(f"❌ Error processing document {doc['id']}: {str(e)}")
                    self.stats['failed'] += 1
        
        # Final statistics
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("=" * 80)
        logger.info("🎉 EMBEDDING COMPLETE!")
        logger.info("=" * 80)
        logger.info(f"📊 Final Statistics:")
        logger.info(f"   Total documents: {self.stats['total']}")
        logger.info(f"   ✅ Successfully embedded: {self.stats['embedded']}")
        logger.info(f"   ⚠️  Duplicates skipped: {self.stats['duplicates']}")
        logger.info(f"   ⏭️  Other skipped: {self.stats['skipped'] - self.stats['duplicates']}")
        logger.info(f"   ❌ Failed: {self.stats['failed']}")
        logger.info(f"   ⏱️  Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")
        
        if self.stats['embedded'] > 0:
            avg_time = duration / self.stats['embedded']
            logger.info(f"   ⚡ Average time per document: {avg_time:.2f} seconds")
        
        logger.info("=" * 80)
        
        # Verify embeddings
        if self.stats['embedded'] > 0:
            self.verify_embeddings()
    
    def verify_embeddings(self):
        """Verify embeddings were stored correctly"""
        logger.info("🔍 Verifying embeddings in database...")
        
        db = SessionLocal()
        try:
            from sqlalchemy import func
            
            # Check total embeddings
            total = db.query(func.count(DocumentEmbedding.id)).scalar()
            logger.info(f"   Total embeddings in database: {total}")
            
            # Check dimension of recent embeddings
            recent = db.query(DocumentEmbedding).order_by(
                DocumentEmbedding.id.desc()
            ).limit(5).all()
            
            if recent:
                dims = [len(emb.embedding) for emb in recent]
                logger.info(f"   Recent embedding dimensions: {dims}")
                
                if all(d == 1024 for d in dims):
                    logger.info("   ✅ All embeddings have correct dimension (1024)")
                else:
                    logger.warning(f"   ⚠️  Dimension mismatch detected: {set(dims)}")
            
        except Exception as e:
            logger.error(f"   ❌ Error verifying embeddings: {str(e)}")
        finally:
            db.close()


def verify_embedding_config():
    """Verify embedding configuration"""
    from Agent.embeddings.embedding_config import get_model_info, ACTIVE_MODEL
    
    logger.info("=" * 80)
    logger.info("📋 EMBEDDING CONFIGURATION")
    logger.info("=" * 80)
    logger.info(get_model_info())
    logger.info("=" * 80)
    
    if ACTIVE_MODEL != "gemini-embedding":
        logger.warning(f"⚠️  Active model is '{ACTIVE_MODEL}', not 'gemini-embedding'")
        logger.warning("To use Gemini, set ACTIVE_MODEL='gemini-embedding' in embedding_config.py")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            logger.info("Aborted by user")
            return False
    
    return True


def main():
    """Main function"""
    logger.info("=" * 80)
    logger.info("🚀 PARALLEL DOCUMENT EMBEDDING SCRIPT")
    logger.info("🌐 Using Google Gemini Multilingual Embeddings")
    logger.info("=" * 80)
    logger.info(f"Workers: {NUM_WORKERS}")
    logger.info(f"Embedding dimension: 1024 (768 native + 256 padding)")
    logger.info(f"Log file: embed_all_documents.log")
    logger.info("=" * 80)
    
    # Verify embedding configuration
    if not verify_embedding_config():
        return
    
    # Check if Google API key is set
    if not os.getenv("GOOGLE_API_KEY"):
        logger.error("❌ GOOGLE_API_KEY not found in environment variables!")
        logger.error("Please set GOOGLE_API_KEY in your .env file")
        return
    
    # Create embedder and run
    embedder = ParallelDocumentEmbedder(num_workers=NUM_WORKERS)
    
    try:
        embedder.embed_all_parallel()
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Interrupted by user")
        logger.info(f"📊 Partial Statistics:")
        logger.info(f"   ✅ Embedded: {embedder.stats['embedded']}")
        logger.info(f"   ⚠️  Duplicates: {embedder.stats['duplicates']}")
        logger.info(f"   ❌ Failed: {embedder.stats['failed']}")
    except Exception as e:
        logger.error(f"❌ Fatal error: {str(e)}")
        raise


if __name__ == "__main__":
    main()
