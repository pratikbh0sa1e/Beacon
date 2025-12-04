"""Conflict detection tools using semantic search and LLM analysis"""
import logging
from typing import List, Dict, Optional
import google.generativeai as genai
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from backend.database import Document, DocumentMetadata
from Agent.lazy_rag.lazy_embedder import LazyEmbedder
from Agent.vector_store.pgvector_store import PGVectorStore
from Agent.embeddings.bge_embedder import BGEEmbedder

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConflictDetector:
    """Tool for detecting conflicts between policy documents using semantic search + LLM"""
    
    def __init__(self, google_api_key: str):
        """
        Initialize the conflict detector
        
        Args:
            google_api_key: Google API key for Gemini
        """
        genai.configure(api_key=google_api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.lazy_embedder = LazyEmbedder()
        self.pgvector_store = PGVectorStore()
        self.embedder = BGEEmbedder()
        logger.info("ConflictDetector initialized with Gemini 2.0 Flash")
    
    def detect_conflicts(
        self,
        document: Dict,
        db: Session,
        user_role: str,
        user_institution_id: Optional[int] = None,
        max_candidates: int = 3
    ) -> Dict:
        """
        Detect conflicts between given document and other documents
        
        Uses lazy embedding strategy:
        1. Search by metadata to find potentially related documents
        2. Embed only top 3 candidates (if not already embedded)
        3. Use semantic search + LLM to detect actual conflicts
        
        Args:
            document: Document dict with 'id', 'title', 'text', 'metadata'
            db: Database session
            user_role: Current user's role
            user_institution_id: Current user's institution ID
            max_candidates: Maximum number of documents to check (default: 3)
        
        Returns:
            List of potential conflicts with severity and recommendations
        """
        try:
            doc_id = document['id']
            logger.info(f"Detecting conflicts for document {doc_id}")
            
            # Step 1: Find potentially related documents using metadata
            candidate_docs = self._find_candidate_documents(
                document,
                db,
                user_role,
                user_institution_id,
                max_candidates
            )
            
            if not candidate_docs:
                return {
                    "status": "success",
                    "document": {
                        "id": document['id'],
                        "title": document['title']
                    },
                    "conflicts": [],
                    "message": "No potentially conflicting documents found",
                    "candidates_checked": 0,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            logger.info(f"Found {len(candidate_docs)} candidate documents for conflict analysis")
            
            # Step 2: Lazy embed candidates (only if not already embedded)
            self._lazy_embed_candidates(candidate_docs)
            
            # Step 3: Use semantic search to find similar content
            similar_docs = self._semantic_search(document, candidate_docs, db)
            
            if not similar_docs:
                return {
                    "status": "success",
                    "document": {
                        "id": document['id'],
                        "title": document['title']
                    },
                    "conflicts": [],
                    "message": "No semantically similar documents found",
                    "candidates_checked": len(candidate_docs),
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Step 4: Use LLM to analyze for actual conflicts
            conflicts = self._analyze_conflicts_with_llm(document, similar_docs)
            
            return {
                "status": "success",
                "document": {
                    "id": document['id'],
                    "title": document['title']
                },
                "conflicts": conflicts,
                "candidates_checked": len(candidate_docs),
                "similar_documents_found": len(similar_docs),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in detect_conflicts: {str(e)}")
            return {
                "error": f"Conflict detection failed: {str(e)}",
                "status": "failed"
            }
    
    def _find_candidate_documents(
        self,
        document: Dict,
        db: Session,
        user_role: str,
        user_institution_id: Optional[int],
        max_candidates: int
    ) -> List[Dict]:
        """
        Find candidate documents using metadata search (BM25-style)
        
        This is the first filter - fast metadata-based search
        """
        try:
            doc_id = document['id']
            metadata = document.get('metadata', {})
            
            # Build search criteria from document metadata
            department = metadata.get('department')
            doc_type = metadata.get('document_type')
            keywords = metadata.get('keywords', [])
            
            # Query for potentially related documents
            query = db.query(Document).filter(Document.id != doc_id)
            
            # Apply role-based access control
            query = self._apply_role_filters(query, user_role, user_institution_id)
            
            # Filter by same department or document type
            metadata_filters = []
            if department:
                metadata_filters.append(DocumentMetadata.department == department)
            if doc_type:
                metadata_filters.append(DocumentMetadata.document_type == doc_type)
            
            if metadata_filters:
                query = query.join(DocumentMetadata).filter(or_(*metadata_filters))
            
            # Get candidates
            candidates = query.limit(max_candidates * 2).all()  # Get more for filtering
            
            # Prepare candidate data
            candidate_docs = []
            for candidate in candidates[:max_candidates]:
                candidate_metadata = db.query(DocumentMetadata).filter(
                    DocumentMetadata.document_id == candidate.id
                ).first()
                
                candidate_docs.append({
                    "id": candidate.id,
                    "title": candidate_metadata.title if candidate_metadata and candidate_metadata.title else candidate.filename,
                    "filename": candidate.filename,
                    "text": candidate.extracted_text or "",
                    "department": candidate_metadata.department if candidate_metadata else None,
                    "document_type": candidate_metadata.document_type if candidate_metadata else None,
                    "approval_status": candidate.approval_status,
                    "visibility_level": candidate.visibility_level
                })
            
            return candidate_docs
            
        except Exception as e:
            logger.error(f"Error finding candidate documents: {str(e)}")
            return []
    
    def _apply_role_filters(
        self,
        query,
        user_role: str,
        user_institution_id: Optional[int]
    ):
        """Apply role-based access control filters to query"""
        
        if user_role == "developer":
            # Full access
            pass
        
        elif user_role == "ministry_admin":
            # Limited access (respects institutional autonomy)
            query = query.filter(
                or_(
                    Document.visibility_level == "public",
                    Document.approval_status == "pending",
                    Document.institution_id == user_institution_id,
                    Document.uploader_id == user_institution_id  # Assuming uploader_id check
                )
            )
        
        elif user_role in ["university_admin", "document_officer"]:
            # Public + their institution
            query = query.filter(
                or_(
                    Document.visibility_level == "public",
                    Document.institution_id == user_institution_id
                )
            )
        
        elif user_role == "student":
            # Approved public + their institution's approved institution_only
            query = query.filter(
                and_(
                    Document.approval_status == "approved",
                    or_(
                        Document.visibility_level == "public",
                        and_(
                            Document.visibility_level == "institution_only",
                            Document.institution_id == user_institution_id
                        )
                    )
                )
            )
        
        elif user_role == "public_viewer":
            # Only approved public
            query = query.filter(
                and_(
                    Document.approval_status == "approved",
                    Document.visibility_level == "public"
                )
            )
        
        return query
    
    def _lazy_embed_candidates(self, candidate_docs: List[Dict]):
        """
        Lazy embed candidate documents (only if not already embedded)
        
        This implements the lazy embedding strategy
        """
        for candidate in candidate_docs:
            doc_id = candidate['id']
            
            # Check if already embedded
            status = self.lazy_embedder.check_embedding_status(doc_id)
            
            if status == 'not_embedded':
                logger.info(f"Lazy embedding candidate document {doc_id}")
                result = self.lazy_embedder.embed_document(doc_id)
                
                if result['status'] == 'success':
                    logger.info(f"Embedded candidate {doc_id}: {result['num_chunks']} chunks")
                else:
                    logger.warning(f"Failed to embed candidate {doc_id}: {result.get('message')}")
            else:
                logger.info(f"Document {doc_id} already embedded, skipping")
    
    def _semantic_search(
        self,
        document: Dict,
        candidate_docs: List[Dict],
        db: Session
    ) -> List[Dict]:
        """
        Use semantic search to find documents with similar content
        
        This is the second filter - semantic similarity
        """
        try:
            # Generate embedding for source document's key content
            doc_text = document.get('text', '')[:2000]  # Use first 2000 chars
            query_embedding = self.embedder.embed(doc_text)
            
            # Search in pgvector for similar chunks
            candidate_ids = [doc['id'] for doc in candidate_docs]
            
            similar_results = self.pgvector_store.search(
                query_embedding=query_embedding,
                top_k=10,
                document_ids=candidate_ids,  # Only search within candidates
                db=db
            )
            
            # Group by document and get top similar documents
            doc_scores = {}
            for result in similar_results:
                doc_id = result['document_id']
                score = result['score']
                
                if doc_id not in doc_scores or score > doc_scores[doc_id]:
                    doc_scores[doc_id] = score
            
            # Filter documents with similarity > 0.7 (likely related content)
            similar_doc_ids = [
                doc_id for doc_id, score in doc_scores.items()
                if score > 0.7
            ]
            
            # Return full document data for similar documents
            similar_docs = [
                doc for doc in candidate_docs
                if doc['id'] in similar_doc_ids
            ]
            
            logger.info(f"Found {len(similar_docs)} semantically similar documents")
            return similar_docs
            
        except Exception as e:
            logger.error(f"Error in semantic search: {str(e)}")
            return []
    
    def _analyze_conflicts_with_llm(
        self,
        document: Dict,
        similar_docs: List[Dict]
    ) -> List[Dict]:
        """
        Use LLM to analyze for actual conflicts
        
        This is the final step - deep conflict analysis
        """
        try:
            prompt = self._build_conflict_analysis_prompt(document, similar_docs)
            
            logger.info(f"Analyzing conflicts with LLM for {len(similar_docs)} similar documents")
            response = self.model.generate_content(prompt)
            
            # Parse response
            conflicts = self._parse_conflict_response(response.text, similar_docs)
            
            return conflicts
            
        except Exception as e:
            logger.error(f"Error in LLM conflict analysis: {str(e)}")
            return []
    
    def _build_conflict_analysis_prompt(
        self,
        document: Dict,
        similar_docs: List[Dict]
    ) -> str:
        """Build prompt for LLM conflict analysis"""
        
        prompt = f"""You are a policy conflict detection expert. Analyze the following documents for CONFLICTS, CONTRADICTIONS, or INCONSISTENCIES.

SOURCE DOCUMENT:
Title: {document['title']}
Content: {document.get('text', '')[:2000]}

POTENTIALLY CONFLICTING DOCUMENTS:
"""
        
        for i, doc in enumerate(similar_docs, 1):
            prompt += f"\n--- DOCUMENT {i}: {doc['title']} ---\n"
            prompt += f"Content: {doc.get('text', '')[:1500]}\n"
        
        prompt += """

TASK:
Identify any conflicts, contradictions, or inconsistencies between the SOURCE DOCUMENT and the other documents.

CONFLICT TYPES:
- contradiction: Direct opposing statements
- overlap: Duplicate or overlapping policies
- inconsistency: Different approaches to same issue
- outdated: Newer policy supersedes older one

OUTPUT FORMAT (JSON):
{
  "conflicts": [
    {
      "conflicting_document_id": document_number,
      "conflicting_document_title": "title",
      "conflict_type": "contradiction|overlap|inconsistency|outdated",
      "severity": "high|medium|low",
      "description": "detailed description of the conflict",
      "source_excerpt": "relevant text from source document",
      "conflicting_excerpt": "relevant text from conflicting document",
      "recommendation": "how to resolve the conflict"
    }
  ]
}

IMPORTANT:
- Only report ACTUAL conflicts, not minor differences
- Provide specific excerpts as evidence
- Assign appropriate severity levels
- Provide actionable recommendations

Provide ONLY the JSON output, no additional text.
"""
        
        return prompt
    
    def _parse_conflict_response(
        self,
        response_text: str,
        similar_docs: List[Dict]
    ) -> List[Dict]:
        """Parse LLM response into structured conflict list"""
        
        try:
            import json
            import re
            
            # Extract JSON from response
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
            else:
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group(0)
                else:
                    json_text = response_text
            
            # Parse JSON
            parsed = json.loads(json_text)
            
            # Map document numbers to actual IDs
            conflicts = []
            for conflict in parsed.get('conflicts', []):
                doc_num = conflict.get('conflicting_document_id')
                
                # Get actual document ID (doc_num is 1-indexed)
                if isinstance(doc_num, int) and 1 <= doc_num <= len(similar_docs):
                    actual_doc = similar_docs[doc_num - 1]
                    
                    conflicts.append({
                        "conflicting_document_id": actual_doc['id'],
                        "conflicting_document_title": actual_doc['title'],
                        "conflict_type": conflict.get('conflict_type', 'unknown'),
                        "severity": conflict.get('severity', 'medium'),
                        "description": conflict.get('description', ''),
                        "source_excerpt": conflict.get('source_excerpt', ''),
                        "conflicting_excerpt": conflict.get('conflicting_excerpt', ''),
                        "recommendation": conflict.get('recommendation', '')
                    })
            
            return conflicts
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            return []
        
        except Exception as e:
            logger.error(f"Error parsing conflict response: {str(e)}")
            return []


# Convenience function for easy import
def create_conflict_detector(google_api_key: str) -> ConflictDetector:
    """Create and return a ConflictDetector instance"""
    return ConflictDetector(google_api_key)
