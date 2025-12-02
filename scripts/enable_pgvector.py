"""Enable pgvector extension and create document_embeddings table"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from backend.database import engine, Base, DocumentEmbedding

def enable_pgvector():
    """Enable pgvector extension in PostgreSQL"""
    print("Enabling pgvector extension...")
    
    with engine.begin() as conn:
        # Enable pgvector extension
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        print("✅ pgvector extension enabled")

def create_tables():
    """Create document_embeddings table"""
    print("Creating document_embeddings table...")
    
    # Create all tables (will only create missing ones)
    Base.metadata.create_all(bind=engine)
    print("✅ document_embeddings table created")

def main():
    try:
        enable_pgvector()
        create_tables()
        print("\n✅ Database setup complete!")
        print("You can now use pgvector for centralized vector storage.")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nMake sure:")
        print("1. PostgreSQL has pgvector extension installed")
        print("2. Database credentials in .env are correct")
        print("3. You have necessary permissions")
        sys.exit(1)

if __name__ == "__main__":
    main()
