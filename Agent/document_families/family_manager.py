"""Document Family Management System for Versioning and Deduplication"""
import logging
import hashlib
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from backend.database import (
    SessionLocal, Document, DocumentFamily, DocumentMetadata, 
    DocumentEmbedding
)
from Agent.embeddings.bge_embedder import BGEEmbedder
from Agent.metadata.extractor import MetadataExtractor

logger = logging.getLogger(__name__)


class DocumentFamilyManager:
    """Manages document families for versioning and deduplication"""
    
    def __init__(self):
        self.embedder = BGEEmbedder()
        self.metadata_extractor = MetadataExtractor()
        
    def calculate_content_hash(self, text: str) -> str:
        """Calculate SHA256 hash of document content"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def find_or_create_family(
        self, 
        document_id: int, 
        title: str, 
        content: str,
        source_url: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Tuple[int, bool]:
        """
        Find existing family or create new one for document
        
        Returns:
            Tuple[family_id, is_new_family]
        """
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True
            
        try:
            # Calculate content hash
            content_hash = self.calculate_content_hash(content)
            
            # Check if document with same hash already exists
            existing_doc = db.query(Document).filter(
                Document.content_hash == content_hash
            ).first()
            
            if existing_doc and existing_doc.document_family_id:
                logger.info(f"Found existing document with same hash, using family {existing_doc.document_family_id}")
                return existing_doc.document_family_id, False
            
            # Extract canonical title and metadata
            canonical_title = self._extract_canonical_title(title, content)
            category, ministry = self._extract_category_and_ministry(content)
            
            # Search for similar families by title similarity
            similar_family = self._find_similar_family(canonical_title, category, ministry, db)
            
            if similar_family:
                logger.info(f"Found similar family {similar_family.id} for document {document_id}")
                return similar_family.id, False
            
            # Create new family
            family = DocumentFamily(
                canonical_title=canonical_title,
                category=category,
                ministry=ministry,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(family)
            db.flush()  # Get the ID
            
            # Generate family centroid embedding
            family_embedding = self._generate_family_embedding(content)
            family.family_centroid_embedding = family_embedding.tolist()
            
            db.commit()
            
            logger.info(f"Created new family {family.id} for document {document_id}")
            return family.id, True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error in find_or_create_family: {str(e)}")
            raise
        finally:
            if close_db:
                db.close()
    
    def add_document_to_family(
        self,
        document_id: int,
        family_id: int,
        content: str,
        source_url: Optional[str] = None,
        last_modified_at_source: Optional[datetime] = None,
        db: Optional[Session] = None
    ) -> Dict:
        """Add document to family with version management"""
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True
            
        try:
            # Get document
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                raise ValueError(f"Document {document_id} not found")
            
            # Calculate content hash
            content_hash = self.calculate_content_hash(content)
            
            # Check if this exact content already exists in the family
            existing_version = db.query(Document).filter(
                and_(
                    Document.document_family_id == family_id,
                    Document.content_hash == content_hash
                )
            ).first()
            
            if existing_version:
                logger.info(f"Document {document_id} is duplicate of {existing_version.id}")
                return {
                    "status": "duplicate",
                    "existing_document_id": existing_version.id,
                    "message": "Document already exists in family"
                }
            
            # Get latest version in family
            latest_version = db.query(Document).filter(
                and_(
                    Document.document_family_id == family_id,
                    Document.is_latest_version == True
                )
            ).first()
            
            # Determine version number
            if latest_version:
                # Parse version number and increment
                try:
                    current_version = float(latest_version.version_number or "1.0")
                    new_version = str(current_version + 0.1)
                except:
                    new_version = "1.1"
                
                # Mark previous version as not latest
                latest_version.is_latest_version = False
                
                # Set supersession relationships
                document.supersedes_id = latest_version.id
                latest_version.superseded_by_id = document.id
                
            else:
                new_version = "1.0"
            
            # Update document with family information
            document.document_family_id = family_id
            document.version_number = new_version
            document.is_latest_version = True
            document.content_hash = content_hash
            document.source_url = source_url
            document.last_modified_at_source = last_modified_at_source
            
            # Update family centroid
            self._update_family_centroid(family_id, db)
            
            db.commit()
            
            logger.info(f"Added document {document_id} to family {family_id} as version {new_version}")
            
            return {
                "status": "added",
                "family_id": family_id,
                "version_number": new_version,
                "is_latest": True,
                "supersedes": latest_version.id if latest_version else None
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error adding document to family: {str(e)}")
            raise
        finally:
            if close_db:
                db.close()
    
    def check_for_updates(
        self,
        source_url: str,
        content: str,
        last_modified_at_source: Optional[datetime] = None,
        db: Optional[Session] = None
    ) -> Dict:
        """Check if document from URL is new or updated version"""
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True
            
        try:
            # Find existing document by URL
            existing_doc = db.query(Document).filter(
                Document.source_url == source_url
            ).first()
            
            if not existing_doc:
                return {"status": "new", "message": "Document not seen before"}
            
            # Calculate new content hash
            new_hash = self.calculate_content_hash(content)
            
            # Check if content changed
            if existing_doc.content_hash == new_hash:
                return {
                    "status": "unchanged",
                    "document_id": existing_doc.id,
                    "message": "Document content unchanged"
                }
            
            # Check if source modification date is newer
            if (last_modified_at_source and 
                existing_doc.last_modified_at_source and
                last_modified_at_source <= existing_doc.last_modified_at_source):
                return {
                    "status": "unchanged",
                    "document_id": existing_doc.id,
                    "message": "Source not modified since last scrape"
                }
            
            return {
                "status": "updated",
                "existing_document_id": existing_doc.id,
                "family_id": existing_doc.document_family_id,
                "message": "Document has been updated at source"
            }
            
        except Exception as e:
            logger.error(f"Error checking for updates: {str(e)}")
            raise
        finally:
            if close_db:
                db.close()
    
    def get_family_documents(
        self,
        family_id: int,
        include_superseded: bool = False,
        db: Optional[Session] = None
    ) -> List[Dict]:
        """Get all documents in a family"""
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True
            
        try:
            query = db.query(Document, DocumentMetadata).outerjoin(
                DocumentMetadata, Document.id == DocumentMetadata.document_id
            ).filter(Document.document_family_id == family_id)
            
            if not include_superseded:
                query = query.filter(Document.is_latest_version == True)
            
            query = query.order_by(desc(Document.version_number))
            
            results = []
            for doc, metadata in query.all():
                results.append({
                    "id": doc.id,
                    "filename": doc.filename,
                    "version_number": doc.version_number,
                    "is_latest_version": doc.is_latest_version,
                    "content_hash": doc.content_hash,
                    "source_url": doc.source_url,
                    "last_modified_at_source": doc.last_modified_at_source,
                    "uploaded_at": doc.uploaded_at,
                    "approval_status": doc.approval_status,
                    "title": metadata.title if metadata else None,
                    "summary": metadata.summary if metadata else None
                })
            
            return results
            
        finally:
            if close_db:
                db.close()
    
    def _extract_canonical_title(self, title: str, content: str) -> str:
        """Extract canonical title from document"""
        # Clean and normalize title
        canonical = title.strip()
        
        # Remove common prefixes/suffixes
        prefixes_to_remove = [
            "notification", "circular", "order", "guidelines", 
            "policy", "scheme", "amendment", "corrigendum"
        ]
        
        for prefix in prefixes_to_remove:
            if canonical.lower().startswith(prefix):
                canonical = canonical[len(prefix):].strip()
                break
        
        # Remove year patterns from title for better grouping
        import re
        canonical = re.sub(r'\b(19|20)\d{2}\b', '', canonical).strip()
        canonical = re.sub(r'\s+', ' ', canonical)  # Normalize whitespace
        
        return canonical[:500]  # Limit length
    
    def _extract_category_and_ministry(self, content: str) -> Tuple[str, str]:
        """Extract category and ministry from content"""
        # Use metadata extractor
        try:
            metadata = self.metadata_extractor.extract_metadata(content, "document.pdf")
            category = metadata.get('document_type', 'policy')
            ministry = metadata.get('department', 'Unknown')
            return category, ministry
        except:
            return 'policy', 'Unknown'
    
    def _find_similar_family(
        self,
        canonical_title: str,
        category: str,
        ministry: str,
        db: Session
    ) -> Optional[DocumentFamily]:
        """Find similar existing family"""
        # First try exact title match
        exact_match = db.query(DocumentFamily).filter(
            DocumentFamily.canonical_title == canonical_title
        ).first()
        
        if exact_match:
            return exact_match
        
        # Try fuzzy matching with same category/ministry
        similar_families = db.query(DocumentFamily).filter(
            and_(
                DocumentFamily.category == category,
                DocumentFamily.ministry == ministry
            )
        ).all()
        
        # Use simple string similarity
        from difflib import SequenceMatcher
        best_match = None
        best_score = 0.0
        
        for family in similar_families:
            score = SequenceMatcher(None, canonical_title.lower(), 
                                  family.canonical_title.lower()).ratio()
            if score > 0.8 and score > best_score:  # 80% similarity threshold
                best_score = score
                best_match = family
        
        return best_match
    
    def _generate_family_embedding(self, content: str) -> np.ndarray:
        """Generate embedding for family centroid"""
        # Use first 1000 characters for family embedding
        sample_text = content[:1000]
        embedding = self.embedder.embed_text(sample_text)
        return np.array(embedding)
    
    def _update_family_centroid(self, family_id: int, db: Session):
        """Update family centroid embedding based on all documents"""
        try:
            # Get all document embeddings in family
            embeddings = db.query(DocumentEmbedding).join(
                Document, DocumentEmbedding.document_id == Document.id
            ).filter(
                Document.document_family_id == family_id
            ).limit(10).all()  # Limit to avoid memory issues
            
            if embeddings:
                # Calculate centroid
                embedding_vectors = [np.array(emb.embedding) for emb in embeddings]
                centroid = np.mean(embedding_vectors, axis=0)
                
                # Update family
                family = db.query(DocumentFamily).filter(
                    DocumentFamily.id == family_id
                ).first()
                
                if family:
                    family.family_centroid_embedding = centroid.tolist()
                    family.updated_at = datetime.utcnow()
                    
        except Exception as e:
            logger.error(f"Error updating family centroid: {str(e)}")


def process_scraped_document(
    document_id: int,
    title: str,
    content: str,
    source_url: Optional[str] = None,
    last_modified_at_source: Optional[datetime] = None
) -> Dict:
    """
    Process a scraped document through the family management system
    
    This is the main entry point for web scraping integration
    """
    manager = DocumentFamilyManager()
    db = SessionLocal()
    
    try:
        # Check if this is an update to existing document
        if source_url:
            update_check = manager.check_for_updates(
                source_url, content, last_modified_at_source, db
            )
            
            if update_check["status"] == "unchanged":
                return update_check
            elif update_check["status"] == "updated":
                # Add as new version to existing family
                return manager.add_document_to_family(
                    document_id,
                    update_check["family_id"],
                    content,
                    source_url,
                    last_modified_at_source,
                    db
                )
        
        # Find or create family for new document
        family_id, is_new_family = manager.find_or_create_family(
            document_id, title, content, source_url, db
        )
        
        # Add document to family
        result = manager.add_document_to_family(
            document_id, family_id, content, source_url, 
            last_modified_at_source, db
        )
        
        result["is_new_family"] = is_new_family
        return result
        
    except Exception as e:
        logger.error(f"Error processing scraped document: {str(e)}")
        raise
    finally:
        db.close()