#!/usr/bin/env python3
"""
Check the actual schema of web_scraping_sources table
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database import SessionLocal

def check_web_scraping_schema():
    """Check what columns exist in web_scraping_sources table"""
    print("🔍 Checking web_scraping_sources table schema")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        # Get table schema
        result = db.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'web_scraping_sources'
            ORDER BY ordinal_position;
        """)
        
        columns = result.fetchall()
        
        print(f"📋 Found {len(columns)} columns:")
        for col in columns:
            print(f"   - {col[0]} ({col[1]}) {'NULL' if col[2] == 'YES' else 'NOT NULL'}")
        
        # Check if pagination_enabled exists
        pagination_exists = any(col[0] == 'pagination_enabled' for col in columns)
        max_pages_exists = any(col[0] == 'max_pages' for col in columns)
        
        print(f"\n🎯 Key columns:")
        print(f"   pagination_enabled: {'✅ EXISTS' if pagination_exists else '❌ MISSING'}")
        print(f"   max_pages: {'✅ EXISTS' if max_pages_exists else '❌ MISSING'}")
        
        # Count existing sources
        try:
            result = db.execute("SELECT COUNT(*) FROM web_scraping_sources")
            count = result.fetchone()[0]
            print(f"\n📊 Total sources: {count}")
            
            if count > 0:
                result = db.execute("SELECT id, name, url FROM web_scraping_sources LIMIT 3")
                sources = result.fetchall()
                print(f"\n📋 Sample sources:")
                for source in sources:
                    print(f"   {source[0]}: {source[1]}")
                    print(f"      URL: {source[2]}")
        except Exception as e:
            print(f"❌ Error querying sources: {e}")
        
    except Exception as e:
        print(f"❌ Error checking schema: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_web_scraping_schema()