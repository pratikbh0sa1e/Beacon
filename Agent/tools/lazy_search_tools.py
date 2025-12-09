"""Lazy RAG search tools - search with on-demand embedding"""
import logging
from typing import List, Dict, Optional
from pathlib import Path
import os
from rank_bm25 import BM25Okapi

from Agent.retrieval.hybrid_retriever import HybridRetriever
from Agent.embeddings.bge_embedder import BGEEmbedder
from Agent.vector_store.pgvector_store import PGVectorStore
from Agent.metadata.reranker import DocumentReranker
from Agent.lazy_rag.lazy_embedder import LazyEmbedder

# Setup logging
log_dir = Path("Agent/agent_logs")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "lazy_search.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize shared components
embedder = BGEEmbedder()
retriever = HybridRetriever(vector_weight=0.7, bm25_weight=0.3)
reranker = DocumentReranker(provider="gemini")
lazy_embedder = LazyEmbedder()
pgvector_store = PGVectorStore()


def search_documents_lazy(query: str, top_k: int = 5, user_role: Optional[str] = None, user_institution_id: Optional[int] = None) -> str:
    """
    Lazy RAG search with role-based filtering using pgvector
    
    Args:
        query: The search query
        top_k: Number of results to return
        user_role: User's role for access control
        user_institution_id: User's institution ID
    
    Returns:
        Formatted search results with citations including approval status
    """
    logger.info(f"Lazy search for query: '{query}' (role={user_role}, institution={user_institution_id})")
    
    try:
        from backend.database import SessionLocal, DocumentMetadata, Document, DocumentEmbedding
        db = SessionLocal()
        
        # Step 1: Check if there are any unembed documents that user can access
        # Get documents user has access to that aren't embedded yet
        query_docs = db.query(Document, DocumentMetadata).join(
            DocumentMetadata, Document.id == DocumentMetadata.document_id
        ).filter(
            DocumentMetadata.embedding_status != 'embedded',
            DocumentMetadata.metadata_status == 'ready',  # Only embed if metadata is ready
            Document.approval_status.in_(['approved', 'pending'])
        )
        
        # Apply role-based filters to find which docs user can access
        from backend.constants.roles import DEVELOPER, MINISTRY_ADMIN, UNIVERSITY_ADMIN
        if user_role == DEVELOPER:
            pass  # Can access all
        elif user_role == MINISTRY_ADMIN:
            query_docs = query_docs.filter(
                Document.visibility_level.in_(['public', 'restricted', 'institution_only'])
            )
        elif user_role == UNIVERSITY_ADMIN:
            from sqlalchemy import or_, and_
            query_docs = query_docs.filter(
                or_(
                    Document.visibility_level == 'public',
                    and_(
                        Document.visibility_level.in_(['institution_only', 'restricted']),
                        Document.institution_id == user_institution_id
                    )
                )
            )
        else:
            from sqlalchemy import or_, and_
            filters = [Document.visibility_level == 'public']
            if user_institution_id:
                filters.append(
                    and_(
                        Document.visibility_level == 'institution_only',
                        Document.institution_id == user_institution_id
                    )
                )
            query_docs = query_docs.filter(or_(*filters))
        
        unembed_docs = query_docs.all()  # Get all unembed docs user can access
        
        # Step 2: Rank documents by metadata relevance using BM25
        if unembed_docs:
            logger.info(f"Found {len(unembed_docs)} unembed documents, ranking by metadata...")
            
            # Build BM25 corpus from metadata
            documents = []
            corpus = []
            for doc, meta in unembed_docs:
                doc_dict = {
                    "doc": doc,
                    "meta": meta,
                    "id": doc.id,
                    "title": meta.title,
                    "filename": doc.filename
                }
                documents.append(doc_dict)
                
                # Create searchable text from metadata
                text_for_bm25 = f"{meta.title or ''} {meta.bm25_keywords or ''} {meta.summary or ''} {meta.department or ''}".lower()
                corpus.append(text_for_bm25.split())
            
            # Rank using BM25
            from rank_bm25 import BM25Okapi
            bm25 = BM25Okapi(corpus)
            query_tokens = query.lower().split()
            bm25_scores = bm25.get_scores(query_tokens)
            
            # Sort by relevance score
            ranked_indices = bm25_scores.argsort()[::-1]  # Descending order
            ranked_docs = [documents[i] for i in ranked_indices]
            
            # Take top 3 most relevant documents to embed
            top_docs_to_embed = ranked_docs[:3]
            
            logger.info(f"Ranked documents by metadata. Top 3 to embed: {[d['id'] for d in top_docs_to_embed]}")
            
            # Step 3: Lazy embed top-ranked documents
            for doc_dict in top_docs_to_embed:
                doc = doc_dict['doc']
                meta = doc_dict['meta']
                try:
                    logger.info(f"Lazy embedding document {doc.id}: {doc.filename} (ranked by metadata)")
                    result = lazy_embedder.embed_document(doc.id)
                    if result['status'] == 'success':
                        logger.info(f"Embedded doc {doc.id}: {result['num_chunks']} chunks")
                    else:
                        logger.warning(f"Failed to embed doc {doc.id}: {result.get('message')}")
                except Exception as e:
                    logger.error(f"Error embedding doc {doc.id}: {str(e)}")
        
        # Step 4: Generate query embedding
        import numpy as np
        query_embedding = embedder.embed_text(query)
        if isinstance(query_embedding, list):
            query_embedding = np.array(query_embedding)
        
        # Step 5: Search pgvector with role-based filtering
        results = pgvector_store.search(
            query_embedding=query_embedding,
            top_k=top_k * 2,  # Get more results for reranking
            user_role=user_role,
            user_institution_id=user_institution_id,
            db=db
        )
        
        if not results:
            db.close()
            return "No relevant documents found matching your access permissions."
        
        logger.info(f"PGVector returned {len(results)} results")
        
        # Step 6: Get document metadata for results
        doc_ids = list(set([r['document_id'] for r in results]))
        doc_metadata = db.query(Document, DocumentMetadata).join(
            DocumentMetadata, Document.id == DocumentMetadata.document_id
        ).filter(Document.id.in_(doc_ids)).all()
        
        doc_info_map = {}
        for doc, meta in doc_metadata:
            doc_info_map[doc.id] = {
                "title": meta.title if meta else doc.filename,
                "filename": doc.filename,
                "approval_status": doc.approval_status,
                "visibility_level": doc.visibility_level
            }
        
        # Step 7: Enhance results with document info
        enhanced_results = []
        for result in results:
            doc_id = result['document_id']
            if doc_id in doc_info_map:
                result.update(doc_info_map[doc_id])
                enhanced_results.append(result)
        
        # Take top_k after enhancement
        top_results = enhanced_results[:top_k]
        
        db.close()
        
        # Step 8: Format results with approval status
        formatted = f"Found {len(top_results)} relevant results:\n\n"
        for i, result in enumerate(top_results, 1):
            approval_badge = "✅ Approved" if result['approval_status'] == 'approved' else "⏳ Pending Approval"
            formatted += f"**Result {i}** (Confidence: {result['score']:.2%}) [{approval_badge}]\n"
            formatted += f"Source: {result.get('filename', 'Unknown')}\n"
            formatted += f"Document ID: {result['document_id']}\n"
            formatted += f"Document: {result.get('title', 'Unknown')}\n"
            formatted += f"Approval Status: {result['approval_status']}\n"
            formatted += f"Visibility: {result['visibility_level']}\n"
            formatted += f"Text: {result['text'][:300]}...\n\n"
        
        logger.info(f"Returned {len(top_results)} results")
        return formatted
        
    except Exception as e:
        logger.error(f"Error in lazy search: {str(e)}")
        return f"Error searching documents: {str(e)}"


def search_specific_document_lazy(document_id: int, query: str, top_k: int = 5, user_role: Optional[str] = None, user_institution_id: Optional[int] = None) -> str:
    """
    Search within a specific document using pgvector with role-based access
    
    Args:
        document_id: The document ID to search in
        query: The search query
        top_k: Number of results to return
        user_role: User's role for access control
        user_institution_id: User's institution ID
    
    Returns:
        Formatted search results from the specific document with approval status
    """
    logger.info(f"Lazy search in doc {document_id}: '{query}' (role={user_role})")
    
    try:
        from backend.database import SessionLocal, DocumentMetadata, Document, DocumentEmbedding
        db = SessionLocal()
        
        # Get document and check access
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            db.close()
            return f"Document {document_id} not found."
        
        # Check if user has access to this document
        from Agent.vector_store.pgvector_store import PGVectorStore
        temp_store = PGVectorStore()
        filters = temp_store._build_role_filters(user_role, user_institution_id)
        
        # Verify access
        access_query = db.query(Document).filter(Document.id == document_id)
        if filters is not None:
            # Apply same filters to document table
            if user_role == "ministry_admin":
                access_query = access_query.filter(
                    Document.visibility_level.in_(['public', 'restricted', 'institution_only'])
                )
            elif user_role == "university_admin":
                from sqlalchemy import or_, and_
                access_query = access_query.filter(
                    or_(
                        Document.visibility_level == 'public',
                        and_(
                            Document.visibility_level.in_(['institution_only', 'restricted']),
                            Document.institution_id == user_institution_id
                        )
                    )
                )
            else:
                from sqlalchemy import or_, and_
                access_filters = [Document.visibility_level == 'public']
                if user_institution_id:
                    access_filters.append(
                        and_(
                            Document.visibility_level == 'institution_only',
                            Document.institution_id == user_institution_id
                        )
                    )
                access_query = access_query.filter(or_(*access_filters))
        
        if not access_query.first():
            db.close()
            return f"Access denied: You don't have permission to access document {document_id}."
        
        # Check if embeddings exist in pgvector
        embedding_count = db.query(DocumentEmbedding).filter(
            DocumentEmbedding.document_id == document_id
        ).count()
        
        if embedding_count == 0:
            logger.info(f"Document {document_id} not embedded in pgvector, embedding now...")
            # Trigger lazy embedding
            try:
                result = lazy_embedder.embed_document(document_id)
                if result['status'] == 'success':
                    logger.info(f"Successfully embedded doc {document_id}: {result['num_chunks']} chunks")
                    # Refresh embedding count
                    embedding_count = db.query(DocumentEmbedding).filter(
                        DocumentEmbedding.document_id == document_id
                    ).count()
                    if embedding_count == 0:
                        db.close()
                        return f"Document {document_id} was embedded but no chunks were created. The document may be empty or unreadable."
                else:
                    db.close()
                    return f"Failed to embed document {document_id}: {result.get('message', 'Unknown error')}"
            except Exception as e:
                logger.error(f"Error embedding doc {document_id}: {str(e)}")
                db.close()
                return f"Error embedding document {document_id}: {str(e)}"
        
        # Generate query embedding
        import numpy as np
        query_embedding = embedder.embed_text(query)
        if isinstance(query_embedding, list):
            query_embedding = np.array(query_embedding)
        
        # Search only this document's embeddings
        results = db.query(DocumentEmbedding).filter(
            DocumentEmbedding.document_id == document_id
        ).order_by(
            DocumentEmbedding.embedding.cosine_distance(query_embedding.tolist())
        ).limit(top_k).all()
        
        if not results:
            db.close()
            return f"No relevant information found in document {document_id}."
        
        # Get document metadata
        metadata = db.query(DocumentMetadata).filter(
            DocumentMetadata.document_id == document_id
        ).first()
        
        doc_title = metadata.title if metadata else doc.filename
        approval_status = doc.approval_status
        
        db.close()
        
        # Format results
        approval_badge = "✅ Approved" if approval_status == 'approved' else "⏳ Pending Approval"
        formatted = f"Found {len(results)} results in Document {document_id} [{approval_badge}]:\n\n"
        for i, result in enumerate(results, 1):
            import numpy as np
            distance = np.linalg.norm(query_embedding - np.array(result.embedding))
            score = 1.0 / (1.0 + distance)
            
            formatted += f"**Result {i}** (Confidence: {score:.2%})\n"
            formatted += f"Source: {doc.filename}\n"
            formatted += f"Document: {doc_title}\n"
            formatted += f"Approval Status: {approval_status}\n"
            formatted += f"Chunk: {result.chunk_index}\n"
            formatted += f"Text: {result.chunk_text[:300]}...\n\n"
        
        logger.info(f"Returned {len(results)} results from doc {document_id}")
        return formatted
        
    except Exception as e:
        logger.error(f"Error in lazy search for doc {document_id}: {str(e)}")
        return f"Error searching document: {str(e)}"
