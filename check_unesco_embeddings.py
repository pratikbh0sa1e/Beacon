#!/usr/bin/env python3
"""Check if UNESCO documents are embedded"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database import SessionLocal, Document, DocumentMetadata, DocumentEmbedding

def check_unesco_embeddings():
    """Check if UNESCO documents have embeddings"""
    
    print("🔍 Checking UNESCO Document Embeddings")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Get UNESCO documents
        unesco_docs = db.query(Document, DocumentMetadata).outerjoin(
            DocumentMetadata, Document.id == DocumentMetadata.document_id
        ).filter(
            DocumentMetadata.title.ilike('%UNESCO%')
        ).all()
        
        print(f"📊 Found {len(unesco_docs)} UNESCO documents")
        
        for doc, meta in unesco_docs:
            print(f"\n📄 Document ID: {doc.id}")
            print(f"   Title: {meta.title}")
            print(f"   Approval: {doc.approval_status}")
            print(f"   Visibility: {doc.visibility_level}")
            
            # Check embeddings
            embedding_count = db.query(DocumentEmbedding).filter(
                DocumentEmbedding.document_id == doc.id
            ).count()
            
            print(f"   Embeddings: {embedding_count} chunks")
            
            if embedding_count == 0:
                print(f"   ❌ NOT EMBEDDED - This is why search fails!")
            else:
                print(f"   ✅ Embedded with {embedding_count} chunks")
        
        # Check total embeddings in system
        total_embeddings = db.query(DocumentEmbedding).count()
        total_docs = db.query(Document).count()
        
        print(f"\n📊 System Statistics:")
        print(f"   Total Documents: {total_docs}")
        print(f"   Total Embeddings: {total_embeddings}")
        print(f"   Embedded Documents: {db.query(DocumentEmbedding.document_id).distinct().count()}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    check_unesco_embeddings()