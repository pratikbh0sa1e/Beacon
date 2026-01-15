#!/usr/bin/env python3
"""
Add missing columns to existing documents table
This is a safe operation that just adds the columns without complex logic
"""
import sys
import os
sys.path.append('.')

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from backend.database import SessionLocal, engine

def add_missing_columns():
    """Add missing columns to documents table"""
    db = SessionLocal()
    
    try:
        print("🔧 Adding missing columns to documents table...")
        
        # Check which columns are missing
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'documents' 
            AND table_schema = 'public'
        """))
        
        existing_columns = {row[0] for row in result.fetchall()}
        print(f"Found {len(existing_columns)} existing columns")
        
        # Define columns to add
        columns_to_add = [
            ("family_id", "INTEGER"),
            ("superseded_by_id", "INTEGER"), 
            ("supersedes_id", "INTEGER"),
            ("content_hash", "VARCHAR(64)"),
            ("source_url", "VARCHAR(1000)"),
            ("last_modified_at_source", "TIMESTAMP")
        ]
        
        # Add missing columns
        for col_name, col_type in columns_to_add:
            if col_name not in existing_columns:
                print(f"Adding column: {col_name}")
                db.execute(text(f"ALTER TABLE documents ADD COLUMN {col_name} {col_type}"))
            else:
                print(f"Column {col_name} already exists")
        
        # Add foreign key constraints if they don't exist
        try:
            print("Adding foreign key constraints...")
            
            # Check existing constraints
            result = db.execute(text("""
                SELECT constraint_name 
                FROM information_schema.table_constraints 
                WHERE table_name = 'documents' 
                AND constraint_type = 'FOREIGN KEY'
            """))
            existing_constraints = {row[0] for row in result.fetchall()}
            
            # Add family_id foreign key
            if 'fk_documents_family_id' not in existing_constraints:
                db.execute(text("""
                    ALTER TABLE documents 
                    ADD CONSTRAINT fk_documents_family_id 
                    FOREIGN KEY (family_id) REFERENCES document_families(id)
                """))
                print("Added family_id foreign key")
            
            # Add superseded_by foreign key
            if 'fk_documents_superseded_by' not in existing_constraints:
                db.execute(text("""
                    ALTER TABLE documents 
                    ADD CONSTRAINT fk_documents_superseded_by 
                    FOREIGN KEY (superseded_by_id) REFERENCES documents(id)
                """))
                print("Added superseded_by foreign key")
            
            # Add supersedes foreign key  
            if 'fk_documents_supersedes' not in existing_constraints:
                db.execute(text("""
                    ALTER TABLE documents 
                    ADD CONSTRAINT fk_documents_supersedes 
                    FOREIGN KEY (supersedes_id) REFERENCES documents(id)
                """))
                print("Added supersedes foreign key")
                
        except Exception as e:
            print(f"Note: Some constraints may already exist: {e}")
        
        # Add indexes
        try:
            print("Adding indexes...")
            
            indexes_to_add = [
                ("idx_documents_family_id", "family_id"),
                ("idx_documents_content_hash", "content_hash"), 
                ("idx_documents_source_url", "source_url"),
                ("idx_documents_family_latest", "family_id, is_latest_version")
            ]
            
            for idx_name, idx_cols in indexes_to_add:
                try:
                    db.execute(text(f"CREATE INDEX IF NOT EXISTS {idx_name} ON documents ({idx_cols})"))
                    print(f"Added index: {idx_name}")
                except Exception as e:
                    print(f"Index {idx_name} may already exist: {e}")
                    
        except Exception as e:
            print(f"Note: Some indexes may already exist: {e}")
        
        db.commit()
        print("✅ Successfully added missing columns and constraints!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error adding columns: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    add_missing_columns()