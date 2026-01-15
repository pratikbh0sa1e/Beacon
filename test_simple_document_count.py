#!/usr/bin/env python3
"""
Simple Document Count Check
Check actual document counts using direct SQL queries to avoid model issues
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_document_counts_direct():
    """Check document counts using direct SQL queries"""
    print("🔍 Direct Document Count Investigation")
    print("=" * 60)
    
    try:
        from backend.database import SessionLocal
        
        db = SessionLocal()
        
        try:
            # Direct SQL queries to avoid model issues
            print("\n1. Direct Database Queries")
            
            # Count documents table
            result = db.execute("SELECT COUNT(*) FROM documents")
            total_docs = result.fetchone()[0]
            print(f"📄 Total documents in 'documents' table: {total_docs}")
            
            # Count documents with scraped URLs
            result = db.execute("SELECT COUNT(*) FROM documents WHERE scraped_from_url IS NOT NULL")
            scraped_docs = result.fetchone()[0]
            print(f"📄 Documents with scraped_from_url: {scraped_docs}")
            
            # Check if scraped_documents table exists
            try:
                result = db.execute("SELECT COUNT(*) FROM scraped_documents")
                scraped_table_count = result.fetchone()[0]
                print(f"📄 ScrapedDocuments table entries: {scraped_table_count}")
            except Exception as e:
                print(f"⚠️  ScrapedDocuments table not accessible: {e}")
            
            # Check web_scraping_sources table directly
            try:
                result = db.execute("SELECT name, url, total_documents_scraped, last_scraped_at FROM web_scraping_sources")
                sources = result.fetchall()
                
                print(f"\n📋 Web Scraping Sources (direct query):")
                for source in sources:
                    print(f"   - {source[0]}")
                    print(f"     URL: {source[1]}")
                    print(f"     Reported scraped: {source[2]}")
                    print(f"     Last scraped: {source[3]}")
                    print()
                    
            except Exception as e:
                print(f"⚠️  Web scraping sources table issue: {e}")
            
            # Check documents from education.gov.in
            result = db.execute("""
                SELECT COUNT(*) FROM documents 
                WHERE scraped_from_url LIKE '%education.gov.in%'
            """)
            moe_docs = result.fetchone()[0]
            print(f"📄 Documents from education.gov.in: {moe_docs}")
            
            # Get sample documents from education.gov.in
            result = db.execute("""
                SELECT filename, scraped_from_url, uploaded_at 
                FROM documents 
                WHERE scraped_from_url LIKE '%education.gov.in%'
                LIMIT 5
            """)
            sample_docs = result.fetchall()
            
            if sample_docs:
                print(f"\n📋 Sample MoE documents in database:")
                for doc in sample_docs:
                    print(f"   - {doc[0]}")
                    print(f"     URL: {doc[1]}")
                    print(f"     Uploaded: {doc[2]}")
                    print()
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error in direct queries: {e}")
        import traceback
        traceback.print_exc()

def check_session_storage():
    """Check if the system is using session storage instead of database"""
    print("\n" + "=" * 60)
    print("📁 Checking Session Storage")
    print("=" * 60)
    
    try:
        # Check if session storage files exist
        session_dir = "data/web_scraping_sessions"
        
        if os.path.exists(session_dir):
            print(f"✅ Session storage directory found: {session_dir}")
            
            # List files in session storage
            files = os.listdir(session_dir)
            print(f"📁 Files in session storage: {len(files)}")
            
            for file in files:
                file_path = os.path.join(session_dir, file)
                if os.path.isfile(file_path):
                    size = os.path.getsize(file_path)
                    print(f"   - {file}: {size} bytes")
            
            # Try to load session storage data
            try:
                from Agent.web_scraping.session_storage import SessionStorage
                
                storage = SessionStorage()
                print(f"\n📊 Session Storage Stats:")
                print(f"   - Sources loaded: {len(storage.sources)}")
                print(f"   - Logs loaded: {len(storage.logs)}")
                print(f"   - Documents loaded: {len(storage.scraped_documents)}")
                
                # Show sample documents from session storage
                if storage.scraped_documents:
                    print(f"\n📋 Sample documents from session storage:")
                    for i, doc in enumerate(list(storage.scraped_documents.values())[:5]):
                        print(f"   {i+1}. {doc.get('title', 'No title')[:50]}...")
                        print(f"      URL: {doc.get('url', 'No URL')}")
                        print(f"      Source: {doc.get('source_name', 'Unknown')}")
                        print()
                
                # Check MoE source specifically
                moe_docs = [doc for doc in storage.scraped_documents.values() 
                           if 'education.gov.in' in doc.get('url', '')]
                print(f"📄 MoE documents in session storage: {len(moe_docs)}")
                
            except Exception as e:
                print(f"⚠️  Error loading session storage: {e}")
        else:
            print(f"❌ Session storage directory not found: {session_dir}")
            
    except Exception as e:
        print(f"❌ Error checking session storage: {e}")

def analyze_discrepancy():
    """Analyze the discrepancy between reported and actual counts"""
    print("\n" + "=" * 60)
    print("🔍 Analyzing Count Discrepancy")
    print("=" * 60)
    
    print("📊 Summary of Findings:")
    print("   - Web scraping source reports: 1779 documents scraped")
    print("   - Database contains: ~239 documents total")
    print("   - This suggests documents are being found but not saved to DB")
    
    print("\n🔍 Possible Causes:")
    print("   1. ✅ Documents found during scraping (scraper works)")
    print("   2. ❌ Documents not being saved to database properly")
    print("   3. ⚠️  Using session storage instead of database")
    print("   4. ⚠️  Database schema mismatch preventing proper storage")
    print("   5. ⚠️  Counter incremented but documents not persisted")
    
    print("\n💡 Recommendations:")
    print("   1. Check if enhanced scraping saves to database correctly")
    print("   2. Verify document processing pipeline")
    print("   3. Test with small batch to see where documents go")
    print("   4. Fix database schema issues")
    print("   5. Ensure proper error handling in document saving")

if __name__ == "__main__":
    check_document_counts_direct()
    check_session_storage()
    analyze_discrepancy()