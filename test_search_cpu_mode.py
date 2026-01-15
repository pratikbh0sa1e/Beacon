#!/usr/bin/env python3
"""Test search with CPU mode to avoid CUDA memory issues"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Force CPU mode
import torch
torch.cuda.is_available = lambda: False

from backend.database import SessionLocal, Document, DocumentMetadata
from sqlalchemy import or_, and_

def test_direct_database_search():
    """Test direct database search for UNESCO document"""
    
    print("🔍 Testing Direct Database Search for UNESCO Document")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Search for UNESCO in titles
        unesco_docs = db.query(Document, DocumentMetadata).outerjoin(
            DocumentMetadata, Document.id == DocumentMetadata.document_id
        ).filter(
            or_(
                Document.filename.ilike('%UNESCO%'),
                DocumentMetadata.title.ilike('%UNESCO%'),
                DocumentMetadata.summary.ilike('%UNESCO%'),
                DocumentMetadata.bm25_keywords.ilike('%UNESCO%')
            )
        ).all()
        
        print(f"📊 Found {len(unesco_docs)} documents with 'UNESCO' in metadata")
        
        for doc, meta in unesco_docs:
            print(f"\n📄 Document ID: {doc.id}")
            print(f"   Filename: {doc.filename}")
            print(f"   Title: {meta.title if meta else 'No metadata'}")
            print(f"   Approval: {doc.approval_status}")
            print(f"   Visibility: {doc.visibility_level}")
            if meta and meta.summary:
                print(f"   Summary: {meta.summary[:200]}...")
        
        # Also search for "Girls" and "Women" and "Education"
        print(f"\n" + "="*60)
        print("🔍 Searching for 'Girls', 'Women', 'Education' keywords")
        
        education_docs = db.query(Document, DocumentMetadata).outerjoin(
            DocumentMetadata, Document.id == DocumentMetadata.document_id
        ).filter(
            or_(
                and_(
                    DocumentMetadata.title.ilike('%girls%'),
                    DocumentMetadata.title.ilike('%women%'),
                    DocumentMetadata.title.ilike('%education%')
                ),
                and_(
                    DocumentMetadata.summary.ilike('%girls%'),
                    DocumentMetadata.summary.ilike('%women%'),
                    DocumentMetadata.summary.ilike('%education%')
                ),
                and_(
                    DocumentMetadata.bm25_keywords.ilike('%girls%'),
                    DocumentMetadata.bm25_keywords.ilike('%women%'),
                    DocumentMetadata.bm25_keywords.ilike('%education%')
                )
            )
        ).all()
        
        print(f"📊 Found {len(education_docs)} documents with girls/women/education keywords")
        
        for doc, meta in education_docs:
            print(f"\n📄 Document ID: {doc.id}")
            print(f"   Filename: {doc.filename}")
            print(f"   Title: {meta.title if meta else 'No metadata'}")
            print(f"   Approval: {doc.approval_status}")
            if meta and meta.summary:
                print(f"   Summary: {meta.summary[:200]}...")
        
        # Search for "prize" keyword
        print(f"\n" + "="*60)
        print("🔍 Searching for 'prize' keyword")
        
        prize_docs = db.query(Document, DocumentMetadata).outerjoin(
            DocumentMetadata, Document.id == DocumentMetadata.document_id
        ).filter(
            or_(
                DocumentMetadata.title.ilike('%prize%'),
                DocumentMetadata.summary.ilike('%prize%'),
                DocumentMetadata.bm25_keywords.ilike('%prize%'),
                Document.filename.ilike('%prize%')
            )
        ).all()
        
        print(f"📊 Found {len(prize_docs)} documents with 'prize' keyword")
        
        for doc, meta in prize_docs:
            print(f"\n📄 Document ID: {doc.id}")
            print(f"   Filename: {doc.filename}")
            print(f"   Title: {meta.title if meta else 'No metadata'}")
            print(f"   Approval: {doc.approval_status}")
            if meta and meta.summary:
                print(f"   Summary: {meta.summary[:200]}...")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    test_direct_database_search()