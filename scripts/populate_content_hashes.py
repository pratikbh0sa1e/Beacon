#!/usr/bin/env python3
"""
Populate content hashes for existing documents
This is needed for deduplication in the family system
"""
import sys
import os
sys.path.append('.')

from dotenv import load_dotenv
load_dotenv()

import hashlib
from backend.database import SessionLocal, Document

def populate_content_hashes():
    """Calculate and populate content hashes for existing documents"""
    db = SessionLocal()
    
    try:
        print("🔢 Populating content hashes for existing documents...")
        
        # Get documents without content hash
        documents = db.query(Document).filter(
            Document.content_hash.is_(None)
        ).all()
        
        print(f"Found {len(documents)} documents without content hash")
        
        if not documents:
            print("All documents already have content hashes!")
            return
        
        updated_count = 0
        
        for i, doc in enumerate(documents, 1):
            try:
                if doc.extracted_text:
                    # Calculate SHA256 hash of content
                    content_hash = hashlib.sha256(
                        doc.extracted_text.encode('utf-8')
                    ).hexdigest()
                    doc.content_hash = content_hash
                    updated_count += 1
                else:
                    # For documents without text, use filename hash
                    content_hash = hashlib.sha256(
                        (doc.filename or "").encode('utf-8')
                    ).hexdigest()
                    doc.content_hash = content_hash
                    updated_count += 1
                
                if i % 50 == 0:
                    db.commit()
                    print(f"Processed {i}/{len(documents)} documents...")
                    
            except Exception as e:
                print(f"Error processing document {doc.id}: {str(e)}")
        
        db.commit()
        print(f"✅ Successfully updated {updated_count} documents with content hashes!")
        
        # Check for duplicates
        print("\n🔍 Checking for duplicate content...")
        
        result = db.execute("""
            SELECT content_hash, COUNT(*) as count
            FROM documents 
            WHERE content_hash IS NOT NULL
            GROUP BY content_hash 
            HAVING COUNT(*) > 1
            ORDER BY count DESC
            LIMIT 10
        """)
        
        duplicates = result.fetchall()
        
        if duplicates:
            print(f"Found {len(duplicates)} sets of duplicate content:")
            for hash_val, count in duplicates:
                print(f"  Hash {hash_val[:16]}... has {count} documents")
        else:
            print("No duplicate content found!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error populating content hashes: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    populate_content_hashes()