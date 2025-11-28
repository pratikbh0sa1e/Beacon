"""
Cleanup script to remove corrupted embeddings
Run this after fixing the lazy_embedder.py to clear old embeddings with wrong metadata structure
"""
import shutil
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.database import SessionLocal, DocumentMetadata

def cleanup_embeddings():
    """Remove all existing embeddings and reset embedding status"""
    
    print("🧹 Starting embedding cleanup...")
    
    # 1. Remove all document embedding directories
    vector_store_path = Path("Agent/vector_store/documents")
    if vector_store_path.exists():
        print(f"📁 Removing {vector_store_path}...")
        shutil.rmtree(vector_store_path)
        print("✅ Removed all embedding files")
    else:
        print("ℹ️  No embedding files found")
    
    # 2. Reset embedding status in database
    db = SessionLocal()
    try:
        metadata_records = db.query(DocumentMetadata).all()
        count = 0
        for meta in metadata_records:
            if meta.embedding_status == 'embedded':
                meta.embedding_status = 'pending'
                count += 1
        
        db.commit()
        print(f"✅ Reset embedding status for {count} documents")
        
    except Exception as e:
        print(f"❌ Error updating database: {e}")
        db.rollback()
    finally:
        db.close()
    
    print("\n🎉 Cleanup complete!")
    print("📝 Next steps:")
    print("   1. Restart your FastAPI server")
    print("   2. Query documents - they will be re-embedded automatically with correct metadata")

if __name__ == "__main__":
    response = input("⚠️  This will delete all embeddings and reset status. Continue? (yes/no): ")
    if response.lower() == 'yes':
        cleanup_embeddings()
    else:
        print("❌ Cleanup cancelled")
