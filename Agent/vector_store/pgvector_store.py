"""PGVector store for centralized vector embeddings"""
import logging
from typing import List, Dict, Optional
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from pgvector.sqlalchemy import Vector

from backend.database import DocumentEmbedding, SessionLocal

logger = logging.getLogger(__name__)


class PGVectorStore:
    """Vector store using PostgreSQL with pgvector extension"""
    
    def __init__(self):
        """Initialize PGVector store"""
        self.dimension = 1024  # BGE-large-en-v1.5 embedding dimension
    
    def add_embeddings(
        self,
        document_id: int,
        chunks: List[str],
        embeddings: np.ndarray,
        metadata_list: List[Dict],
        visibility_level: str,
        institution_id: Optional[int],
        approval_status: str,
        db: Optional[Session] = None
    ) -> int:
        """
        Add embeddings to pgvector
        
        Args:
            document_id: Document ID
            chunks: List of text chunks
            embeddings: Numpy array of embeddings (n_chunks x dimension)
            metadata_list: List of metadata dicts for each chunk
            visibility_level: Document visibility level
            institution_id: Institution ID (can be None)
            approval_status: Document approval status
            db: Optional database session (creates new if None)
        
        Returns:
            Number of embeddings added
        """
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True
        
        try:
            # Delete existing embeddings for this document
            db.query(DocumentEmbedding).filter(
                DocumentEmbedding.document_id == document_id
            ).delete()
            
            # Add new embeddings
            for idx, (chunk, embedding, metadata) in enumerate(zip(chunks, embeddings, metadata_list)):
                # Convert to list if it's a numpy array
                if hasattr(embedding, 'tolist'):
                    embedding_list = embedding.tolist()
                else:
                    embedding_list = embedding  # Already a list
                
                doc_embedding = DocumentEmbedding(
                    document_id=document_id,
                    chunk_index=idx,
                    chunk_text=chunk,
                    embedding=embedding_list,
                    visibility_level=visibility_level,
                    institution_id=institution_id,
                    approval_status=approval_status,
                    chunk_metadata=metadata
                )
                db.add(doc_embedding)
            
            db.commit()
            logger.info(f"Added {len(chunks)} embeddings for document {document_id}")
            return len(chunks)
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error adding embeddings for document {document_id}: {str(e)}")
            raise
        finally:
            if close_db:
                db.close()
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        user_role: Optional[str] = None,
        user_institution_id: Optional[int] = None,
        document_id_filter: Optional[int] = None,
        db: Optional[Session] = None
    ) -> List[Dict]:
        """
        Search for similar embeddings with role-based filtering
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            user_role: User's role for filtering
            user_institution_id: User's institution ID
            document_id_filter: Optional document ID to search within only
            db: Optional database session
        
        Returns:
            List of results with text, score, metadata, document_id
        """
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True
        
        try:
            # Build base query
            query = db.query(DocumentEmbedding)
            
            # Filter by specific document if provided
            if document_id_filter is not None:
                query = query.filter(DocumentEmbedding.document_id == document_id_filter)
            
            # Apply role-based filtering
            if user_role:
                filters = self._build_role_filters(user_role, user_institution_id)
                if filters is not None:
                    query = query.filter(filters)
            
            # Filter by approval status (approved or pending only)
            # Draft, rejected, and changes_requested documents are NOT searchable
            query = query.filter(
                DocumentEmbedding.approval_status.in_(['approved', 'pending'])
            )
            
            # Perform vector similarity search using cosine distance
            # pgvector uses <=> for cosine distance
            query = query.order_by(
                DocumentEmbedding.embedding.cosine_distance(query_embedding.tolist())
            ).limit(top_k)
            
            results = query.all()
            
            # Format results
            formatted_results = []
            for result in results:
                # Calculate similarity score (1 - cosine_distance)
                distance = np.linalg.norm(query_embedding - np.array(result.embedding))
                score = 1.0 / (1.0 + distance)  # Convert distance to similarity
                
                formatted_results.append({
                    "text": result.chunk_text,
                    "score": float(score),
                    "metadata": result.chunk_metadata or {},
                    "document_id": result.document_id,
                    "chunk_index": result.chunk_index,
                    "approval_status": result.approval_status,
                    "visibility_level": result.visibility_level,
                    "institution_id": result.institution_id
                })
            
            logger.info(f"Found {len(formatted_results)} results for query")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching embeddings: {str(e)}")
            raise
        finally:
            if close_db:
                db.close()
    
    def _build_role_filters(self, user_role: str, user_institution_id: Optional[int]):
        """
        Build SQLAlchemy filters based on user role
        
        Args:
            user_role: User's role
            user_institution_id: User's institution ID
        
        Returns:
            SQLAlchemy filter expression or None for no filtering
        """
        from backend.constants.roles import DEVELOPER, MINISTRY_ADMIN, UNIVERSITY_ADMIN
        
        # Developer sees everything
        if user_role == DEVELOPER:
            return None
        
        # MoE Admin sees public, restricted, and institution_only (all institutions)
        elif user_role == MINISTRY_ADMIN:
            return DocumentEmbedding.visibility_level.in_([
                'public', 'restricted', 'institution_only'
            ])
        
        # University Admin sees public + their institution's docs
        elif user_role == UNIVERSITY_ADMIN:
            return or_(
                DocumentEmbedding.visibility_level == 'public',
                and_(
                    DocumentEmbedding.visibility_level.in_(['institution_only', 'restricted']),
                    DocumentEmbedding.institution_id == user_institution_id
                )
            )
        
        # Students and others see public + their institution's institution_only docs
        else:
            filters = [DocumentEmbedding.visibility_level == 'public']
            if user_institution_id:
                filters.append(
                    and_(
                        DocumentEmbedding.visibility_level == 'institution_only',
                        DocumentEmbedding.institution_id == user_institution_id
                    )
                )
            return or_(*filters)
    
    def delete_document_embeddings(self, document_id: int, db: Optional[Session] = None):
        """
        Delete all embeddings for a document
        
        Args:
            document_id: Document ID
            db: Optional database session
        """
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True
        
        try:
            deleted = db.query(DocumentEmbedding).filter(
                DocumentEmbedding.document_id == document_id
            ).delete()
            db.commit()
            logger.info(f"Deleted {deleted} embeddings for document {document_id}")
            return deleted
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting embeddings for document {document_id}: {str(e)}")
            raise
        finally:
            if close_db:
                db.close()
    
    def update_document_metadata(
        self,
        document_id: int,
        visibility_level: Optional[str] = None,
        institution_id: Optional[int] = None,
        approval_status: Optional[str] = None,
        db: Optional[Session] = None
    ):
        """
        Update denormalized metadata for all embeddings of a document
        
        Args:
            document_id: Document ID
            visibility_level: New visibility level
            institution_id: New institution ID
            approval_status: New approval status
            db: Optional database session
        """
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True
        
        try:
            embeddings = db.query(DocumentEmbedding).filter(
                DocumentEmbedding.document_id == document_id
            ).all()
            
            for embedding in embeddings:
                if visibility_level is not None:
                    embedding.visibility_level = visibility_level
                if institution_id is not None:
                    embedding.institution_id = institution_id
                if approval_status is not None:
                    embedding.approval_status = approval_status
            
            db.commit()
            logger.info(f"Updated metadata for {len(embeddings)} embeddings of document {document_id}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating metadata for document {document_id}: {str(e)}")
            raise
        finally:
            if close_db:
                db.close()
    
    def get_stats(self, db: Optional[Session] = None) -> Dict:
        """Get statistics about the vector store"""
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True
        
        try:
            total_embeddings = db.query(DocumentEmbedding).count()
            total_documents = db.query(DocumentEmbedding.document_id).distinct().count()
            
            return {
                "total_embeddings": total_embeddings,
                "total_documents": total_documents,
                "dimension": self.dimension
            }
        finally:
            if close_db:
                db.close()
