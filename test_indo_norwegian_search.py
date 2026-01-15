#!/usr/bin/env python3
"""Test search for Indo-Norwegian document"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database import SessionLocal, Document, DocumentMetadata
from sqlalchemy import or_, and_

def test_indo_norwegian_search():
    """Test searching for Indo-Norwegian document"""
    
    print("🔍 Testing Search for Indo-Norwegian Document")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Search for Indo-Norwegian documents
        queries = [
            "Indo-Norwegian",
            "Norway",
            "Norwegian", 
            "INCP2",
            "Indo Norwegian Cooperation Programme"
        ]
        
        for query in queries:
            print(f"\n📝 Searching for: '{query}'")
            print("-" * 40)
            
            # Search in metadata fields
            docs = db.query(Document, DocumentMetadata).outerjoin(
                DocumentMetadata, Document.id == DocumentMetadata.document_id
            ).filter(
                or_(
                    Document.filename.ilike(f'%{query}%'),
                    DocumentMetadata.title.ilike(f'%{query}%'),
                    DocumentMetadata.summary.ilike(f'%{query}%'),
                    DocumentMetadata.bm25_keywords.ilike(f'%{query}%')
                )
            ).all()
            
            print(f"📊 Found {len(docs)} documents")
            
            for doc, meta in docs:
                print(f"\n📄 Document ID: {doc.id}")
                print(f"   Filename: {doc.filename}")
                print(f"   Title: {meta.title if meta else 'No metadata'}")
                print(f"   Approval: {doc.approval_status}")
                if meta and meta.summary:
                    print(f"   Summary: {meta.summary[:200]}...")
        
        # Also search for the exact title
        print(f"\n" + "="*60)
        print("🔍 Searching for exact title pattern")
        
        exact_docs = db.query(Document, DocumentMetadata).outerjoin(
            DocumentMetadata, Document.id == DocumentMetadata.document_id
        ).filter(
            or_(
                DocumentMetadata.title.ilike('%Indo-Norwegian%'),
                DocumentMetadata.title.ilike('%Cooperation Programme%'),
                Document.filename.ilike('%Indo-Norwegian%'),
                Document.filename.ilike('%INCP%')
            )
        ).all()
        
        print(f"📊 Found {len(exact_docs)} documents with exact patterns")
        
        for doc, meta in exact_docs:
            print(f"\n📄 Document ID: {doc.id}")
            print(f"   Filename: {doc.filename}")
            print(f"   Title: {meta.title if meta else 'No metadata'}")
            print(f"   Approval: {doc.approval_status}")
            if meta and meta.summary:
                print(f"   Summary: {meta.summary[:300]}...")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_indo_norwegian_search()