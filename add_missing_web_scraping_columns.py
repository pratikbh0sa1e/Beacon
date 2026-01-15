#!/usr/bin/env python3
"""
Add missing columns to web_scraping_sources table
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database import SessionLocal

def add_missing_columns():
    """Add missing columns to web_scraping_sources table"""
    print("🔧 Adding missing columns to web_scraping_sources")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        # List of columns to add
        columns_to_add = [
            ("pagination_enabled", "BOOLEAN DEFAULT FALSE NOT NULL"),
            ("max_pages", "INTEGER DEFAULT 10 NOT NULL"),
            ("schedule_type", "VARCHAR(20)"),
            ("schedule_time", "VARCHAR(10)"),
            ("schedule_enabled", "BOOLEAN DEFAULT FALSE NOT NULL"),
            ("next_scheduled_run", "TIMESTAMP")
        ]
        
        for column_name, column_def in columns_to_add:
            try:
                print(f"📝 Adding column: {column_name}")
                
                sql = f"ALTER TABLE web_scraping_sources ADD COLUMN {column_name} {column_def}"
                db.execute(sql)
                db.commit()
                
                print(f"   ✅ Added {column_name}")
                
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"   ⚠️  Column {column_name} already exists")
                else:
                    print(f"   ❌ Error adding {column_name}: {e}")
                db.rollback()
        
        print(f"\n🎯 Verifying columns...")
        
        # Verify the columns were added
        result = db.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'web_scraping_sources'
            AND column_name IN ('pagination_enabled', 'max_pages', 'schedule_type', 'schedule_time', 'schedule_enabled', 'next_scheduled_run')
            ORDER BY column_name;
        """)
        
        added_columns = [row[0] for row in result.fetchall()]
        
        for column_name, _ in columns_to_add:
            if column_name in added_columns:
                print(f"   ✅ {column_name}")
            else:
                print(f"   ❌ {column_name}")
        
        print(f"\n✅ Column addition complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_missing_columns()