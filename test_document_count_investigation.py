#!/usr/bin/env python3
"""
Investigate Document Count Discrepancy
Check why web scraping source shows 1779 documents but DB only has 239
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def investigate_document_counts():
    """Investigate the document count discrepancy"""
    print("🔍 Investigating Document Count Discrepancy")
    print("=" * 60)
    
    try:
        from backend.database import SessionLocal, Document, WebScrapingSource, ScrapedDocument
        
        db = SessionLocal()
        
        try:
            # Check web scraping sources
            print("\n1. Web Scraping Sources Analysis")
            sources = db.query(WebScrapingSource).all()
            
            for source in sources:
                print(f"\n📋 Source: {source.name}")
                print(f"   ID: {source.id}")
                print(f"   URL: {source.url}")
                print(f"   Total documents scraped (reported): {source.total_documents_scraped}")
                print(f"   Last scraped: {source.last_scraped_at}")
                print(f"   Status: {source.last_scrape_status}")
            
            # Check actual documents in database
            print("\n2. Actual Documents in Database")
            
            # Count all documents
            total_docs = db.query(Document).count()
            print(f"📄 Total documents in DB: {total_docs}")
            
            # Count documents by source
            scraped_docs = db.query(Document).filter(
                Document.scraped_from_url.isnot(None)
            ).count()
            print(f"📄 Documents with scraped_from_url: {scraped_docs}")
            
            # Check ScrapedDocument table if it exists
            try:
                scraped_doc_count = db.query(ScrapedDocument).count()
                print(f"📄 ScrapedDocument table entries: {scraped_doc_count}")
                
                # Get sample scraped documents
                sample_scraped = db.query(ScrapedDocument).limit(5).all()
                print(f"\n📋 Sample ScrapedDocument entries:")
                for doc in sample_scraped:
                    print(f"   - {doc.title[:50]}...")
                    print(f"     URL: {doc.url}")
                    print(f"     Source ID: {doc.source_id}")
                    
            except Exception as e:
                print(f"⚠️  ScrapedDocument table issue: {e}")
            
            # Check documents from MoE source specifically
            print("\n3. Documents from MoE Source")
            moe_docs = db.query(Document).filter(
                Document.scraped_from_url.like('%education.gov.in%')
            ).all()
            
            print(f"📄 Documents from education.gov.in: {len(moe_docs)}")
            
            if moe_docs:
                print("📋 Sample MoE documents:")
                for doc in moe_docs[:5]:
                    print(f"   - {doc.filename}")
                    print(f"     URL: {doc.scraped_from_url}")
                    print(f"     Uploaded: {doc.uploaded_at}")
                    print()
            
            # Check document metadata
            print("\n4. Document Metadata Analysis")
            from backend.database import DocumentMetadata
            
            total_metadata = db.query(DocumentMetadata).count()
            print(f"📊 Total document metadata entries: {total_metadata}")
            
            # Check for documents without metadata
            docs_without_metadata = db.query(Document).filter(
                ~Document.id.in_(
                    db.query(DocumentMetadata.document_id)
                )
            ).count()
            print(f"⚠️  Documents without metadata: {docs_without_metadata}")
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error investigating: {e}")
        import traceback
        traceback.print_exc()

def test_actual_scraping():
    """Test the actual scraping process to see what happens"""
    print("\n" + "=" * 60)
    print("🧪 Testing Actual Scraping Process")
    print("=" * 60)
    
    try:
        from backend.database import SessionLocal, WebScrapingSource
        
        db = SessionLocal()
        
        try:
            # Get the MoE source
            moe_source = db.query(WebScrapingSource).filter(
                WebScrapingSource.name.like('%Education%')
            ).first()
            
            if moe_source:
                print(f"🎯 Testing with source: {moe_source.name}")
                print(f"   URL: {moe_source.url}")
                
                # Test enhanced scraping with small limits
                print("\n📡 Running enhanced scraping test (limited)...")
                
                from Agent.web_scraping.enhanced_processor import enhanced_scrape_source
                
                # Run with very small limits for testing
                result = enhanced_scrape_source(
                    source_id=moe_source.id,
                    keywords=None,
                    max_documents=5,  # Very small for testing
                    pagination_enabled=False,  # Disable pagination for quick test
                    max_pages=1,
                    incremental=True
                )
                
                print("✅ Enhanced scraping test completed!")
                print(f"📊 Results: {result}")
                
                # Check database again after scraping
                print("\n📄 Checking database after test scraping...")
                
                total_docs_after = db.query(Document).count()
                scraped_docs_after = db.query(Document).filter(
                    Document.scraped_from_url.isnot(None)
                ).count()
                
                print(f"   Total documents now: {total_docs_after}")
                print(f"   Scraped documents now: {scraped_docs_after}")
                
            else:
                print("❌ No MoE source found")
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error in scraping test: {e}")
        import traceback
        traceback.print_exc()

def check_scraping_logs():
    """Check scraping logs for insights"""
    print("\n" + "=" * 60)
    print("📋 Checking Scraping Logs")
    print("=" * 60)
    
    try:
        from backend.database import SessionLocal, WebScrapingLog
        
        db = SessionLocal()
        
        try:
            # Get recent scraping logs
            logs = db.query(WebScrapingLog).order_by(
                WebScrapingLog.started_at.desc()
            ).limit(10).all()
            
            print(f"📋 Found {len(logs)} recent scraping logs:")
            
            for log in logs:
                print(f"\n🕒 {log.started_at}")
                print(f"   Source: {log.source_name}")
                print(f"   Status: {log.status}")
                print(f"   Documents found: {log.documents_found}")
                print(f"   Documents matched: {log.documents_matched}")
                print(f"   Duration: {log.execution_time_seconds}s")
                if log.error_message:
                    print(f"   Error: {log.error_message}")
                    
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error checking logs: {e}")

if __name__ == "__main__":
    investigate_document_counts()
    check_scraping_logs()
    test_actual_scraping()