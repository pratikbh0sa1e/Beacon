"""
Cleanup script to remove documents from session storage that don't exist in database
"""
import os
import json
from pathlib import Path
from backend.database import SessionLocal, Document

def cleanup_session_storage():
    """Remove documents from session storage that aren't in the database"""
    
    # Path to session storage
    session_storage_path = Path("data/web_scraping_sessions")
    scraped_docs_file = session_storage_path / "scraped_documents.json"
    
    if not scraped_docs_file.exists():
        print("❌ Session storage file not found")
        return
    
    # Load session storage documents
    with open(scraped_docs_file, 'r', encoding='utf-8') as f:
        session_docs = json.load(f)
    
    print(f"📊 Session storage has {len(session_docs)} documents")
    
    # Get all document URLs from database
    db = SessionLocal()
    try:
        db_documents = db.query(Document).all()
        db_urls = {doc.source_url for doc in db_documents if doc.source_url}
        db_s3_keys = {doc.s3_key for doc in db_documents if doc.s3_key}
        
        print(f"📊 Database has {len(db_documents)} documents")
        print(f"📊 Database has {len(db_urls)} unique source URLs")
        print(f"📊 Database has {len(db_s3_keys)} documents with S3 keys")
        
        # Filter session docs - keep only those that exist in DB
        valid_docs = []
        removed_count = 0
        
        for doc in session_docs:
            doc_url = doc.get('url')
            doc_s3_key = doc.get('s3_key')
            
            # Check if document exists in DB by URL or S3 key
            exists_in_db = (
                (doc_url and doc_url in db_urls) or
                (doc_s3_key and doc_s3_key in db_s3_keys)
            )
            
            if exists_in_db:
                valid_docs.append(doc)
            else:
                removed_count += 1
                print(f"🗑️  Removing: {doc.get('title', 'Unknown')[:50]}")
        
        print(f"\n📊 Summary:")
        print(f"   Total in session storage: {len(session_docs)}")
        print(f"   Valid (in DB): {len(valid_docs)}")
        print(f"   Removed (not in DB): {removed_count}")
        
        # Backup original file
        backup_file = session_storage_path / "scraped_documents.backup.json"
        print(f"\n💾 Creating backup: {backup_file}")
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(session_docs, f, indent=2, ensure_ascii=False)
        
        # Save cleaned data
        print(f"💾 Saving cleaned data: {scraped_docs_file}")
        with open(scraped_docs_file, 'w', encoding='utf-8') as f:
            json.dump(valid_docs, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Cleanup complete!")
        print(f"   Session storage now has {len(valid_docs)} documents")
        print(f"   Backup saved to: {backup_file}")
        
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("SESSION STORAGE CLEANUP")
    print("=" * 60)
    print("\nThis will remove documents from session storage that")
    print("don't exist in the database (no S3 link).\n")
    
    response = input("Continue? (y/n): ")
    if response.lower() == 'y':
        cleanup_session_storage()
    else:
        print("❌ Cleanup cancelled")
