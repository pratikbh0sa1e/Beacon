"""Family-Aware RAG Retriever for Enhanced Accuracy"""
import logging
from typing import List, Dict, Optional, Tuple
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from backend.database import (
    SessionLocal, Document, DocumentFamily, DocumentMetadata, 
    DocumentEmbedding
)
from Agent.embeddings.bge_embedder import BGEEmbedder
from Agent.vector_store.pgvector_store import PGVectorStore

logger = logging.getLogger(__name__)


class FamilyAwareRetriever:
    """Enhanced RAG retriever that considers document families and versions"""
    
    def __init__(self):
        self.embedder = BGEEmbedder()
        self.pgvector_store = PGVectorStore()
        
    def search_with_family_awareness(
        self,
        query: str,
        top_k: int = 5,
        user_role: Optional[str] = None,
        user_institution_id: Optional[int] = None,
        prefer_latest: bool = True,
        family_diversity: bool = True,
        db: Optional[Session] = None
    ) -> List[Dict]:
        """
        Search with family awareness for better accuracy
        
        Args:
            query: Search query
            top_k: Number of results to return
            user_role: User's role for access control
            user_institution_id: User's institution ID
            prefer_latest: Whether to prefer latest versions
            family_diversity: Whether to ensure diversity across families
        """
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True
            
        try:
            # Generate query embedding
            query_embedding = self.embedder.embed_text(query)
            if isinstance(query_embedding, list):
                query_embedding = np.array(query_embedding)
            
            # Step 1: Get initial results from pgvector
            initial_results = self.pgvector_store.search(
                query_embedding=query_embedding,
                top_k=top_k * 3,  # Get more results for reranking
                user_role=user_role,
                user_institution_id=user_institution_id,
                db=db
            )
            
            if not initial_results:
                return []
            
            # Step 2: Enhance results with family information
            enhanced_results = self._enhance_with_family_info(initial_results, db)
            
            # Step 3: Apply family-aware ranking
            ranked_results = self._apply_family_ranking(
                enhanced_results, 
                prefer_latest=prefer_latest,
                family_diversity=family_diversity
            )
            
            # Step 4: Return top results
            return ranked_results[:top_k]
            
        finally:
            if close_db:
                db.close()
    
    def search_by_family(
        self,
        family_id: int,
        query: str,
        top_k: int = 5,
        user_role: Optional[str] = None,
        user_institution_id: Optional[int] = None,
        include_all_versions: bool = False,
        db: Optional[Session] = None
    ) -> List[Dict]:
        """Search within a specific document family"""
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True
            
        try:
            # Generate query embedding
            query_embedding = self.embedder.embed_text(query)
            if isinstance(query_embedding, list):
                query_embedding = np.array(query_embedding)
            
            # Get documents in family
            family_query = db.query(Document).filter(
                Document.document_family_id == family_id
            )
            
            if not include_all_versions:
                family_query = family_query.filter(
                    Document.is_latest_version == True
                )
            
            # Apply role-based filtering
            if user_role:
                family_query = self._apply_role_filters(
                    family_query, user_role, user_institution_id
                )
            
            family_docs = family_query.all()
            doc_ids = [doc.id for doc in family_docs]
            
            if not doc_ids:
                return []
            
            # Search embeddings for these documents
            embeddings_query = db.query(DocumentEmbedding).filter(
                DocumentEmbedding.document_id.in_(doc_ids)
            ).order_by(
                DocumentEmbedding.embedding.cosine_distance(query_embedding.tolist())
            ).limit(top_k)
            
            results = []
            for embedding in embeddings_query.all():
                # Get document info
                doc = next((d for d in family_docs if d.id == embedding.document_id), None)
                if not doc:
                    continue
                
                # Calculate similarity score
                distance = np.linalg.norm(query_embedding - np.array(embedding.embedding))
                score = 1.0 / (1.0 + distance)
                
                results.append({
                    "text": embedding.chunk_text,
                    "score": float(score),
                    "document_id": embedding.document_id,
                    "chunk_index": embedding.chunk_index,
                    "filename": doc.filename,
                    "version_number": doc.version_number,
                    "is_latest_version": doc.is_latest_version,
                    "family_id": family_id,
                    "approval_status": doc.approval_status
                })
            
            return results
            
        finally:
            if close_db:
                db.close()
    
    def find_related_families(
        self,
        query: str,
        top_k: int = 5,
        db: Optional[Session] = None
    ) -> List[Dict]:
        """Find document families related to query"""
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True
            
        try:
            # Generate query embedding
            query_embedding = self.embedder.embed_text(query)
            if isinstance(query_embedding, list):
                query_embedding = np.array(query_embedding)
            
            # Search family centroids
            families = db.query(DocumentFamily).filter(
                DocumentFamily.family_centroid_embedding.isnot(None)
            ).all()
            
            family_scores = []
            for family in families:
                if family.family_centroid_embedding:
                    centroid = np.array(family.family_centroid_embedding)
                    distance = np.linalg.norm(query_embedding - centroid)
                    score = 1.0 / (1.0 + distance)
                    
                    # Get document count in family
                    doc_count = db.query(Document).filter(
                        Document.document_family_id == family.id
                    ).count()
                    
                    # Get latest document info
                    latest_doc = db.query(Document, DocumentMetadata).outerjoin(
                        DocumentMetadata, Document.id == DocumentMetadata.document_id
                    ).filter(
                        and_(
                            Document.document_family_id == family.id,
                            Document.is_latest_version == True
                        )
                    ).first()
                    
                    family_scores.append({
                        "family_id": family.id,
                        "canonical_title": family.canonical_title,
                        "category": family.category,
                        "ministry": family.ministry,
                        "score": float(score),
                        "document_count": doc_count,
                        "latest_version": latest_doc[0].version_number if latest_doc else None,
                        "latest_title": latest_doc[1].title if latest_doc and latest_doc[1] else None,
                        "created_at": family.created_at,
                        "updated_at": family.updated_at
                    })
            
            # Sort by score and return top results
            family_scores.sort(key=lambda x: x["score"], reverse=True)
            return family_scores[:top_k]
            
        finally:
            if close_db:
                db.close()
    
    def get_family_evolution(
        self,
        family_id: int,
        db: Optional[Session] = None
    ) -> Dict:
        """Get the evolution history of a document family"""
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True
            
        try:
            # Get family info
            family = db.query(DocumentFamily).filter(
                DocumentFamily.id == family_id
            ).first()
            
            if not family:
                return {"error": "Family not found"}
            
            # Get all documents in family ordered by version
            documents = db.query(Document, DocumentMetadata).outerjoin(
                DocumentMetadata, Document.id == DocumentMetadata.document_id
            ).filter(
                Document.document_family_id == family_id
            ).order_by(Document.version_number).all()
            
            evolution = {
                "family_id": family_id,
                "canonical_title": family.canonical_title,
                "category": family.category,
                "ministry": family.ministry,
                "created_at": family.created_at,
                "updated_at": family.updated_at,
                "versions": []
            }
            
            for doc, metadata in documents:
                version_info = {
                    "document_id": doc.id,
                    "version_number": doc.version_number,
                    "is_latest_version": doc.is_latest_version,
                    "filename": doc.filename,
                    "title": metadata.title if metadata else doc.filename,
                    "uploaded_at": doc.uploaded_at,
                    "source_url": doc.scraped_from_url,
                    "last_modified_at_source": doc.last_modified_at_source,
                    "approval_status": doc.approval_status,
                    "content_hash": doc.content_hash,
                    "supersedes_id": doc.supersedes_id,
                    "superseded_by_id": doc.superseded_by_id
                }
                
                if metadata:
                    version_info.update({
                        "summary": metadata.summary,
                        "keywords": metadata.keywords,
                        "document_type": metadata.document_type,
                        "department": metadata.department
                    })
                
                evolution["versions"].append(version_info)
            
            return evolution
            
        finally:
            if close_db:
                db.close()
    
    def _enhance_with_family_info(self, results: List[Dict], db: Session) -> List[Dict]:
        """Enhance search results with family information"""
        enhanced = []
        
        for result in results:
            doc_id = result["document_id"]
            
            # Get document and family info
            doc_info = db.query(Document, DocumentFamily, DocumentMetadata).outerjoin(
                DocumentFamily, Document.document_family_id == DocumentFamily.id
            ).outerjoin(
                DocumentMetadata, Document.id == DocumentMetadata.document_id
            ).filter(Document.id == doc_id).first()
            
            if doc_info:
                doc, family, metadata = doc_info
                
                enhanced_result = result.copy()
                enhanced_result.update({
                    "filename": doc.filename,
                    "version_number": doc.version_number,
                    "is_latest_version": doc.is_latest_version,
                    "family_id": doc.document_family_id,
                    "family_title": family.canonical_title if family else None,
                    "family_category": family.category if family else None,
                    "family_ministry": family.ministry if family else None,
                    "document_title": metadata.title if metadata else doc.filename,
                    "document_type": metadata.document_type if metadata else None,
                    "department": metadata.department if metadata else None,
                    "content_hash": doc.content_hash,
                    "source_url": doc.source_url
                })
                
                enhanced.append(enhanced_result)
        
        return enhanced
    
    def _apply_family_ranking(
        self,
        results: List[Dict],
        prefer_latest: bool = True,
        family_diversity: bool = True
    ) -> List[Dict]:
        """Apply family-aware ranking to results"""
        if not results:
            return results
        
        # Group by family
        family_groups = {}
        for result in results:
            family_id = result.get("family_id")
            if family_id not in family_groups:
                family_groups[family_id] = []
            family_groups[family_id].append(result)
        
        # Rank within each family
        for family_id, family_results in family_groups.items():
            # Sort by score first
            family_results.sort(key=lambda x: x["score"], reverse=True)
            
            if prefer_latest:
                # Boost latest versions
                for result in family_results:
                    if result.get("is_latest_version"):
                        result["score"] *= 1.2  # 20% boost for latest versions
        
        # Flatten and sort all results
        all_results = []
        for family_results in family_groups.values():
            all_results.extend(family_results)
        
        all_results.sort(key=lambda x: x["score"], reverse=True)
        
        # Apply family diversity if requested
        if family_diversity:
            diverse_results = []
            used_families = set()
            
            # First pass: one result per family
            for result in all_results:
                family_id = result.get("family_id")
                if family_id not in used_families:
                    diverse_results.append(result)
                    used_families.add(family_id)
            
            # Second pass: fill remaining slots
            remaining_slots = len(all_results) - len(diverse_results)
            for result in all_results:
                if result not in diverse_results and remaining_slots > 0:
                    diverse_results.append(result)
                    remaining_slots -= 1
            
            return diverse_results
        
        return all_results
    
    def _apply_role_filters(self, query, user_role: str, user_institution_id: Optional[int]):
        """Apply role-based filtering to document query"""
        from backend.constants.roles import DEVELOPER, MINISTRY_ADMIN, UNIVERSITY_ADMIN
        
        if user_role == DEVELOPER:
            return query  # No filtering for developers
        elif user_role == MINISTRY_ADMIN:
            return query.filter(
                Document.visibility_level.in_(['public', 'restricted', 'institution_only'])
            )
        elif user_role == UNIVERSITY_ADMIN:
            return query.filter(
                or_(
                    Document.visibility_level == 'public',
                    and_(
                        Document.visibility_level.in_(['institution_only', 'restricted']),
                        Document.institution_id == user_institution_id
                    )
                )
            )
        else:
            # Students and public users
            filters = [Document.visibility_level == 'public']
            if user_institution_id:
                filters.append(
                    and_(
                        Document.visibility_level == 'institution_only',
                        Document.institution_id == user_institution_id
                    )
                )
            return query.filter(or_(*filters))


# Integration functions for existing RAG system
def enhanced_search_documents(
    query: str,
    top_k: int = 5,
    user_role: Optional[str] = None,
    user_institution_id: Optional[int] = None,
    prefer_latest: bool = True
) -> str:
    """
    Enhanced search function that can replace existing search_documents_lazy
    """
    retriever = FamilyAwareRetriever()
    
    try:
        results = retriever.search_with_family_awareness(
            query=query,
            top_k=top_k,
            user_role=user_role,
            user_institution_id=user_institution_id,
            prefer_latest=prefer_latest,
            family_diversity=True
        )
        
        if not results:
            return "No relevant documents found matching your access permissions."
        
        # Format results
        formatted = f"Found {len(results)} relevant results:\n\n"
        for i, result in enumerate(results, 1):
            approval_badge = "✅ Approved" if result['approval_status'] == 'approved' else "⏳ Pending Approval"
            version_info = f"v{result.get('version_number', '1.0')}"
            if result.get('is_latest_version'):
                version_info += " (Latest)"
            
            formatted += f"**Result {i}** (Confidence: {result['score']:.2%}) [{approval_badge}]\n"
            formatted += f"Source: {result.get('filename', 'Unknown')}\n"
            formatted += f"Document ID: {result['document_id']}\n"
            formatted += f"Document: {result.get('document_title', 'Unknown')}\n"
            formatted += f"Version: {version_info}\n"
            formatted += f"Family: {result.get('family_title', 'Unknown')}\n"
            formatted += f"Category: {result.get('family_category', 'Unknown')}\n"
            formatted += f"Ministry: {result.get('family_ministry', 'Unknown')}\n"
            formatted += f"Approval Status: {result['approval_status']}\n"
            formatted += f"Text: {result['text'][:300]}...\n\n"
        
        return formatted
        
    except Exception as e:
        logger.error(f"Error in enhanced search: {str(e)}")
        return f"Error searching documents: {str(e)}"