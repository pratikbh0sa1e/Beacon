#!/usr/bin/env python3
"""Quick test of family creation"""
import sys
sys.path.append('.')
from dotenv import load_dotenv
load_dotenv()

from backend.database import SessionLocal, Document, DocumentFamily
from Agent.document_families.family_manager import process_scraped_document

def test_family_creation():
    db = SessionLocal()
    
    try:
        # Get first 5 documents without families
        docs = db.query(Document).filter(Document.document_family_id.is_(None)).limit(5).all()
        print(f'Processing {len(docs)} documents into families...')
        
        for doc in docs:
            if doc.extracted_text:
                try:
                    result = process_scraped_document(
                        doc.id, 
                        doc.filename, 
                        doc.extracted_text[:1000],  # Use first 1000 chars
                        doc.scraped_from_url
                    )
                    print(f'Doc {doc.id}: {result["status"]} - Family {result.get("family_id")}')
                except Exception as e:
                    print(f'Error processing doc {doc.id}: {e}')
        
        # Check results
        family_count = db.query(DocumentFamily).count()
        docs_with_families = db.query(Document).filter(Document.document_family_id.isnot(None)).count()
        
        print(f'\nResults:')
        print(f'Total families: {family_count}')
        print(f'Documents with families: {docs_with_families}')
        
    finally:
        db.close()

if __name__ == "__main__":
    test_family_creation()