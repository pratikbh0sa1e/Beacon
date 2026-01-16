"""
Comprehensive cleanup script to remove orphaned files
- Removes files from Supabase storage that don't exist in database
- Removes documents from session storage that don't exist in database
"""
import os
import json
from pathlib import Path
from backend.database import SessionLocal, Document
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def cleanup_supabase_storage():
    """Remove files from Supabase storage that don't exist in database"""
    
    # Initialize Supabase client
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    bucket_name = os.getenv("SUPABASE_BUCKET_NAME", "Docs")
    
    if not supabase_url or not supabase_key:
        print("❌ Supabase credentials not found in .env")
        return 0
    
    supabase = create_client(supabase_url, supabase_key)
    
    print("\n" + "=" * 60)
    print("CLEANING SUPABASE STORAGE")
    print("=" * 60)
    
    # Get all files from Supabase bucket
    try:
        print(f"\n📦 Fetching files from bucket: {bucket_name}")
        response = supabase.storage.from_(bucket_name).list()
        
        if not response:
            print("❌ No files found in bucket or error accessing bucket")
            return 0
        
        storage_files = response
        print(f"📊 Found {len(storage_files)} files in Supabase storage")
        
    except Exception as e:
        print(f"❌ Error accessing Supabase storage: {e}")
        return 0
    
    # Get all S3 URLs and file paths from database
    db = SessionLocal()
    try:
        db_documents = db.query(Document).filter(
            (Document.s3_url.isnot(None)) | (Document.file_path.isnot(None))
        ).all()
        
        # Extract filenames from s3_url and file_path
        db_filenames = set()
        for doc in db_documents:
            if doc.s3_url:
                # Extract filename from URL
                filename = doc.s3_url.split('/')[-1]
                db_filenames.add(filename)
            if doc.file_path:
                # Extract filename from path
                filename = doc.file_path.split('/')[-1]
                db_filenames.add(filename)
        
        print(f"📊 Database has {len(db_documents)} documents with files")
        print(f"📊 Database has {len(db_filenames)} unique filenames")
        
        # Find orphaned files
        orphaned_files = []
        for file_obj in storage_files:
            file_name = file_obj.get('name')
            
            # Skip if it's a folder
            if not file_name or file_obj.get('id') is None:
                continue
            
            # Check if file exists in database
            if file_name not in db_filenames:
                orphaned_files.append(file_name)
        
        print(f"\n📊 Found {len(orphaned_files)} orphaned files (not in database)")
        
        if not orphaned_files:
            print("✅ No orphaned files to remove!")
            return 0
        
        # Show sample of files to be deleted
        print(f"\n🗑️  Sample of files to be deleted (first 10):")
        for i, filename in enumerate(orphaned_files[:10], 1):
            print(f"   {i}. {filename[:80]}")
        
        if len(orphaned_files) > 10:
            print(f"   ... and {len(orphaned_files) - 10} more")
        
        # Confirm deletion
        print(f"\n⚠️  WARNING: This will delete {len(orphaned_files)} files from Supabase!")
        response = input("Continue with deletion? (y/n): ")
        
        if response.lower() not in ['y', 'yes']:
            print("❌ Deletion cancelled")
            return 0
        
        # Delete orphaned files
        print(f"\n🗑️  Deleting orphaned files...")
        deleted_count = 0
        failed_count = 0
        
        for filename in orphaned_files:
            try:
                supabase.storage.from_(bucket_name).remove([filename])
                deleted_count += 1
                
                if deleted_count % 10 == 0:
                    print(f"   Deleted {deleted_count}/{len(orphaned_files)} files...")
                
            except Exception as e:
                failed_count += 1
                print(f"   ❌ Failed to delete {filename[:50]}: {e}")
        
        print(f"\n✅ Supabase cleanup complete!")
        print(f"   Deleted: {deleted_count} files")
        print(f"   Failed: {failed_count} files")
        
        return deleted_count
        
    finally:
        db.close()


def cleanup_session_storage():
    """Remove documents from session storage that don't exist in database"""
    
    print("\n" + "=" * 60)
    print("CLEANING SESSION STORAGE")
    print("=" * 60)
    
    session_storage_path = Path("data/web_scraping_sessions")
    scraped_docs_file = session_storage_path / "scraped_docs.json"
    
    if not scraped_docs_file.exists():
        print("❌ Session storage file not found")
        return 0
    
    # Load session storage documents
    with open(scraped_docs_file, 'r', encoding='utf-8') as f:
        session_docs = json.load(f)
    
    print(f"\n📊 Session storage has {len(session_docs)} documents")
    
    # Get all document URLs and filenames from database
    db = SessionLocal()
    try:
        db_documents = db.query(Document).all()
        db_urls = {doc.source_url for doc in db_documents if doc.source_url}
        
        # Extract filenames from s3_url and file_path
        db_filenames = set()
        for doc in db_documents:
            if doc.s3_url:
                filename = doc.s3_url.split('/')[-1]
                db_filenames.add(filename)
            if doc.file_path:
                filename = doc.file_path.split('/')[-1]
                db_filenames.add(filename)
        
        print(f"📊 Database has {len(db_documents)} documents")
        
        # Filter session docs - keep only those that exist in DB
        valid_docs = []
        removed_count = 0
        
        for doc in session_docs:
            doc_url = doc.get('url')
            doc_filename = doc.get('s3_key') or doc.get('filename')
            
            # Check if document exists in DB by URL or filename
            exists_in_db = (
                (doc_url and doc_url in db_urls) or
                (doc_filename and doc_filename in db_filenames)
            )
            
            if exists_in_db:
                valid_docs.append(doc)
            else:
                removed_count += 1
        
        print(f"\n📊 Summary:")
        print(f"   Total in session storage: {len(session_docs)}")
        print(f"   Valid (in DB): {len(valid_docs)}")
        print(f"   Removed (not in DB): {removed_count}")
        
        if removed_count == 0:
            print("✅ No orphaned documents in session storage!")
            return 0
        
        # Backup original file
        backup_file = session_storage_path / "scraped_docs.backup.json"
        print(f"\n💾 Creating backup: {backup_file}")
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(session_docs, f, indent=2, ensure_ascii=False)
        
        # Save cleaned data
        print(f"💾 Saving cleaned data: {scraped_docs_file}")
        with open(scraped_docs_file, 'w', encoding='utf-8') as f:
            json.dump(valid_docs, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Session storage cleanup complete!")
        print(f"   Session storage now has {len(valid_docs)} documents")
        
        return removed_count
        
    finally:
        db.close()


def main():
    """Main cleanup function"""
    print("=" * 60)
    print("COMPREHENSIVE CLEANUP SCRIPT")
    print("=" * 60)
    print("\nThis script will:")
    print("1. Remove orphaned files from Supabase storage")
    print("2. Remove orphaned documents from session storage")
    print("\nOrphaned = Files/docs that don't exist in database\n")
    
    response = input("Continue? (y/n): ")
    if response.lower() != 'y':
        print("❌ Cleanup cancelled")
        return
    
    # Cleanup Supabase storage
    supabase_deleted = cleanup_supabase_storage()
    
    # Cleanup session storage
    session_removed = cleanup_session_storage()
    
    # Final summary
    print("\n" + "=" * 60)
    print("CLEANUP SUMMARY")
    print("=" * 60)
    print(f"Supabase files deleted: {supabase_deleted}")
    print(f"Session docs removed: {session_removed}")
    print("\n✅ Cleanup complete!")


if __name__ == "__main__":
    main()
