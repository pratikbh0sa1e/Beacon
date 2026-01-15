#!/usr/bin/env python3
"""
Migrate existing documents to document families system
This script will:
1. Add missing columns to existing documents
2. Create document families for existing documents
3. Group similar documents into families
4. Set version numbers and latest version flags
5. Calculate content hashes
"""
import sys
import os
sys.path.append('.')

from dotenv import load_dotenv
load_dotenv()

import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher
import re

from backend.database import SessionLocal, Document, DocumentFamily, DocumentMetadata
from Agent.embeddings.bge_embedder import BGEEmbedder
from Agent.metadata.extractor import MetadataExtractor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DocumentFamilyMigrator:
    """Migrate existing documents to family structure"""
    
    def __init__(self):
        self.embedder = BGEEmbedder()
        self.metadata_extractor = MetadataExtractor()
        
    def migrate_all_documents(self):
        """Main migration function"""
        db = SessionLocal()
        
        try:
            logger.info("Starting document family migration...")
            
            # Step 1: Get all documents that need migration
            documents = db.query(Document).filter(
                Document.document_family_id.is_(None)
            ).all()
            
            logger.info(f"Found {len(documents)} documents to migrate")
            
            if not documents:
                logger.info("No documents need migration")
                return
            
            # Step 2: Add missing columns data
            self._populate_missing_columns(documents, db)
            
            # Step 3: Create families and assign documents
            self._create_families_and_assign(documents, db)
            
            # Step 4: Set version numbers and latest flags
            self._set_version_numbers(db)
            
            # Step 5: Update family centroids
            self._update_family_centroids(db)
            
            db.commit()
            logger.info("Migration completed successfully!")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Migration failed: {str(e)}")
            raise
        finally:
            db.close()
    
    def _populate_missing_columns(self, documents: List[Document], db):
        """Populate missing columns for existing documents"""
        logger.info("Populating missing columns...")
        
        for i, doc in enumerate(documents, 1):
            try:
                logger.info(f"Processing document {i}/{len(documents)}: {doc.filename}")
                
                # Calculate content hash
                if not doc.content_hash and doc.extracted_text:
                    doc.content_hash = hashlib.sha256(
                        doc.extracted_text.encode('utf-8')
                    ).hexdigest()
                
                # Set default version number if missing
                if not doc.version_number:
                    doc.version_number = "1.0"
                
                # Set latest version flag (will be updated later)
                if doc.is_latest_version is None:
                    doc.is_latest_version = True
                
                # Extract source URL from filename or metadata if it looks like a URL
                if not doc.scraped_from_url:
                    # Check if filename contains URL-like patterns
                    if any(pattern in doc.filename.lower() for pattern in ['http', 'www.', '.gov', '.edu']):
                        # This might be a scraped document, but we can't recover the URL
                        pass
                
                if i % 50 == 0:
                    db.commit()  # Commit in batches
                    logger.info(f"Processed {i} documents...")
                    
            except Exception as e:
                logger.error(f"Error processing document {doc.id}: {str(e)}")
        
        db.commit()
        logger.info("Finished populating missing columns")
    
    def _create_families_and_assign(self, documents: List[Document], db):
        """Create families and assign documents"""
        logger.info("Creating families and assigning documents...")
        
        # Group documents by similarity
        family_groups = self._group_documents_by_similarity(documents, db)
        
        logger.info(f"Created {len(family_groups)} family groups")
        
        for group_idx, doc_group in enumerate(family_groups, 1):
            try:
                logger.info(f"Processing family group {group_idx}/{len(family_groups)} with {len(doc_group)} documents")
                
                # Create family for this group
                family = self._create_family_for_group(doc_group, db)
                
                # Assign all documents in group to this family
                for doc in doc_group:
                    doc.document_family_id = family.id
                
                if group_idx % 10 == 0:
                    db.commit()
                    logger.info(f"Processed {group_idx} family groups...")
                    
            except Exception as e:
                logger.error(f"Error processing family group {group_idx}: {str(e)}")
        
        db.commit()
        logger.info("Finished creating families")
    
    def _group_documents_by_similarity(self, documents: List[Document], db) -> List[List[Document]]:
        """Group documents by title and content similarity"""
        logger.info("Grouping documents by similarity...")
        
        # Get metadata for all documents
        doc_metadata = {}
        metadata_records = db.query(DocumentMetadata).filter(
            DocumentMetadata.document_id.in_([doc.id for doc in documents])
        ).all()
        
        for meta in metadata_records:
            doc_metadata[meta.document_id] = meta
        
        # Create document info for grouping
        doc_infos = []
        for doc in documents:
            metadata = doc_metadata.get(doc.id)
            
            # Extract canonical title
            title = metadata.title if metadata else doc.filename
            canonical_title = self._extract_canonical_title(title)
            
            # Extract category and ministry
            category = metadata.document_type if metadata else self._guess_category(doc.filename)
            ministry = metadata.department if metadata else self._guess_ministry(doc.filename, doc.extracted_text)
            
            doc_infos.append({
                'document': doc,
                'canonical_title': canonical_title,
                'category': category,
                'ministry': ministry,
                'metadata': metadata
            })
        
        # Group by exact canonical title first
        title_groups = {}
        for doc_info in doc_infos:
            key = (doc_info['canonical_title'].lower(), doc_info['category'], doc_info['ministry'])
            if key not in title_groups:
                title_groups[key] = []
            title_groups[key].append(doc_info)
        
        # Further group by similarity within each title group
        final_groups = []
        for title_group in title_groups.values():
            if len(title_group) == 1:
                final_groups.append([title_group[0]['document']])
            else:
                # Group by content similarity
                similarity_groups = self._group_by_content_similarity(title_group)
                for group in similarity_groups:
                    final_groups.append([info['document'] for info in group])
        
        logger.info(f"Created {len(final_groups)} document groups from {len(documents)} documents")
        return final_groups
    
    def _group_by_content_similarity(self, doc_infos: List[Dict]) -> List[List[Dict]]:
        """Group documents by content similarity"""
        if len(doc_infos) <= 1:
            return [doc_infos]
        
        groups = []
        remaining = doc_infos.copy()
        
        while remaining:
            current_doc = remaining.pop(0)
            current_group = [current_doc]
            
            # Find similar documents
            to_remove = []
            for other_doc in remaining:
                if self._are_documents_similar(current_doc, other_doc):
                    current_group.append(other_doc)
                    to_remove.append(other_doc)
            
            # Remove similar documents from remaining
            for doc in to_remove:
                remaining.remove(doc)
            
            groups.append(current_group)
        
        return groups
    
    def _are_documents_similar(self, doc1: Dict, doc2: Dict) -> bool:
        """Check if two documents are similar enough to be in same family"""
        # Check title similarity
        title_similarity = SequenceMatcher(
            None, 
            doc1['canonical_title'].lower(), 
            doc2['canonical_title'].lower()
        ).ratio()
        
        if title_similarity > 0.8:  # 80% title similarity
            return True
        
        # Check if they have similar keywords or content
        if doc1['metadata'] and doc2['metadata']:
            keywords1 = set(doc1['metadata'].keywords or [])
            keywords2 = set(doc2['metadata'].keywords or [])
            
            if keywords1 and keywords2:
                keyword_overlap = len(keywords1.intersection(keywords2)) / len(keywords1.union(keywords2))
                if keyword_overlap > 0.5:  # 50% keyword overlap
                    return True
        
        # Check content similarity (first 500 chars)
        content1 = doc1['document'].extracted_text[:500] if doc1['document'].extracted_text else ""
        content2 = doc2['document'].extracted_text[:500] if doc2['document'].extracted_text else ""
        
        if content1 and content2:
            content_similarity = SequenceMatcher(None, content1.lower(), content2.lower()).ratio()
            if content_similarity > 0.7:  # 70% content similarity
                return True
        
        return False
    
    def _create_family_for_group(self, doc_group: List[Document], db) -> DocumentFamily:
        """Create a family for a group of documents"""
        # Get the best representative document (longest content or most recent)
        representative_doc = max(doc_group, key=lambda d: (
            len(d.extracted_text or ""),
            d.uploaded_at or datetime.min
        ))
        
        # Get metadata for representative document
        metadata = db.query(DocumentMetadata).filter(
            DocumentMetadata.document_id == representative_doc.id
        ).first()
        
        # Extract family information
        title = metadata.title if metadata else representative_doc.filename
        canonical_title = self._extract_canonical_title(title)
        category = metadata.document_type if metadata else self._guess_category(representative_doc.filename)
        ministry = metadata.department if metadata else self._guess_ministry(
            representative_doc.filename, 
            representative_doc.extracted_text
        )
        
        # Create family
        family = DocumentFamily(
            canonical_title=canonical_title,
            category=category,
            ministry=ministry,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(family)
        db.flush()  # Get the ID
        
        logger.info(f"Created family {family.id}: {canonical_title}")
        return family
    
    def _set_version_numbers(self, db):
        """Set proper version numbers within each family"""
        logger.info("Setting version numbers...")
        
        families = db.query(DocumentFamily).all()
        
        for family in families:
            # Get all documents in family ordered by upload date
            docs = db.query(Document).filter(
                Document.document_family_id == family.id
            ).order_by(Document.uploaded_at).all()
            
            if not docs:
                continue
            
            # Assign version numbers
            for i, doc in enumerate(docs):
                doc.version_number = f"{i + 1}.0"
                doc.is_latest_version = (i == len(docs) - 1)  # Last one is latest
                
                # Set supersession relationships
                if i > 0:
                    doc.supersedes_id = docs[i - 1].id
                    docs[i - 1].superseded_by_id = doc.id
        
        db.commit()
        logger.info("Finished setting version numbers")
    
    def _update_family_centroids(self, db):
        """Update family centroid embeddings"""
        logger.info("Updating family centroids...")
        
        families = db.query(DocumentFamily).all()
        
        for i, family in enumerate(families, 1):
            try:
                # Get latest document in family
                latest_doc = db.query(Document).filter(
                    Document.document_family_id == family.id,
                    Document.is_latest_version == True
                ).first()
                
                if latest_doc and latest_doc.extracted_text:
                    # Generate embedding for family centroid
                    sample_text = latest_doc.extracted_text[:1000]
                    embedding = self.embedder.embed_text(sample_text)
                    family.family_centroid_embedding = embedding
                    family.updated_at = datetime.utcnow()
                
                if i % 10 == 0:
                    db.commit()
                    logger.info(f"Updated {i}/{len(families)} family centroids...")
                    
            except Exception as e:
                logger.error(f"Error updating centroid for family {family.id}: {str(e)}")
        
        db.commit()
        logger.info("Finished updating family centroids")
    
    def _extract_canonical_title(self, title: str) -> str:
        """Extract canonical title from document title"""
        canonical = title.strip()
        
        # Remove common prefixes
        prefixes = [
            "notification", "circular", "order", "guidelines", 
            "policy", "scheme", "amendment", "corrigendum",
            "letter", "memo", "memorandum", "advisory"
        ]
        
        for prefix in prefixes:
            if canonical.lower().startswith(prefix):
                canonical = canonical[len(prefix):].strip()
                canonical = re.sub(r'^[:\-\s]+', '', canonical)
                break
        
        # Remove year patterns
        canonical = re.sub(r'\b(19|20)\d{2}\b', '', canonical)
        canonical = re.sub(r'\s+', ' ', canonical).strip()
        
        # Remove file extensions
        canonical = re.sub(r'\.(pdf|doc|docx|xls|xlsx)$', '', canonical, flags=re.IGNORECASE)
        
        return canonical[:500]
    
    def _guess_category(self, filename: str) -> str:
        """Guess document category from filename"""
        filename_lower = filename.lower()
        
        if any(word in filename_lower for word in ['policy', 'policies']):
            return 'policy'
        elif any(word in filename_lower for word in ['guideline', 'guidelines', 'guide']):
            return 'guideline'
        elif any(word in filename_lower for word in ['circular', 'notification']):
            return 'circular'
        elif any(word in filename_lower for word in ['order', 'orders']):
            return 'order'
        elif any(word in filename_lower for word in ['scheme', 'schemes']):
            return 'scheme'
        elif any(word in filename_lower for word in ['report', 'reports']):
            return 'report'
        else:
            return 'document'
    
    def _guess_ministry(self, filename: str, content: Optional[str]) -> str:
        """Guess ministry from filename and content"""
        text_to_search = f"{filename} {content[:500] if content else ''}".lower()
        
        ministry_patterns = {
            'Ministry of Education': ['education', 'ugc', 'aicte', 'university', 'college'],
            'Ministry of Health': ['health', 'medical', 'hospital', 'healthcare'],
            'Ministry of Finance': ['finance', 'budget', 'tax', 'revenue'],
            'Ministry of Home Affairs': ['home affairs', 'security', 'police'],
            'Ministry of Defence': ['defence', 'defense', 'military', 'army'],
            'Ministry of External Affairs': ['external affairs', 'foreign', 'embassy'],
            'Ministry of Railways': ['railway', 'train', 'rail'],
            'Ministry of Road Transport': ['transport', 'highway', 'road'],
        }
        
        for ministry, keywords in ministry_patterns.items():
            if any(keyword in text_to_search for keyword in keywords):
                return ministry
        
        return 'Unknown Ministry'


def main():
    """Run the migration"""
    print("🚀 Starting Document Family Migration")
    print("=" * 50)
    
    migrator = DocumentFamilyMigrator()
    
    try:
        migrator.migrate_all_documents()
        print("\n✅ Migration completed successfully!")
        
        # Print summary
        db = SessionLocal()
        try:
            total_docs = db.query(Document).count()
            total_families = db.query(DocumentFamily).count()
            docs_with_families = db.query(Document).filter(
                Document.document_family_id.isnot(None)
            ).count()
            
            print(f"\n📊 Migration Summary:")
            print(f"   Total Documents: {total_docs}")
            print(f"   Total Families: {total_families}")
            print(f"   Documents with Families: {docs_with_families}")
            print(f"   Average Documents per Family: {docs_with_families / total_families if total_families > 0 else 0:.1f}")
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        print("Check migration.log for details")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())