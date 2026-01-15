#!/usr/bin/env python3
"""
Test fresh scraping from MoE source
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database import SessionLocal, Document, DocumentMetadata, WebScrapingSource
from Agent.web_scraping.enhanced_processor import enhanced_scrape_source

def test_moe_scraping():
    """Test MoE scraping for new documents"""
    print("🧪 Testing MoE Enhanced Scraping")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Use MoE source (ID 2)
        source_id = 2
        source = db.query(WebScrapingSource).filter(WebScrapingSource.id == source_id).first()
        
        if not source:
            print(f"❌ Source {source_id} not found")
            return
        
        print(f"🎯 Testing with: {source.name}")
        print(f"   URL: {source.url}")
        
        # Count documents before
        docs_before = db.query(Document).count()
        scraped_before = db.query(Document).filter(Document.source_url.isnot(None)).count()
        
        print(f"\n📊 Before scraping:")
        print(f"   Total documents: {docs_before}")
        print(f"   Scraped documents: {scraped_before}")
        
        # Check recent scraped documents
        recent_scraped = db.query(Document).filter(
            Document.source_url.like('%education.gov.in%')
        ).order_by(Document.uploaded_at.desc()).limit(3).all()
        
        print(f"\n📋 Recent MoE documents:")
        for doc in recent_scraped:
            print(f"   - {doc.filename[:60]}...")
            print(f"     URL: {doc.source_url}")
            print(f"     Uploaded: {doc.uploaded_at}")
        
        # Run enhanced scraping with small limit
        print(f"\n🚀 Starting enhanced scraping (limit 3)...")
        
        result = enhanced_scrape_source(
            source_id=source_id,
            max_documents=3,
            pagination_enabled=False,
            max_pages=1
        )
        
        print(f"\n✅ Scraping Results:")
        print(f"   Status: {result.get('status')}")
        print(f"   Documents discovered: {result.get('documents_discovered', 0)}")
        print(f"   Documents new: {result.get('documents_new', 0)}")
        print(f"   Documents unchanged: {result.get('documents_unchanged', 0)}")
        print(f"   Documents processed: {result.get('documents_processed', 0)}")
        print(f"   Execution time: {result.get('execution_time', 0):.2f}s")
        
        # Count documents after
        docs_after = db.query(Document).count()
        scraped_after = db.query(Document).filter(Document.source_url.isnot(None)).count()
        
        print(f"\n📊 After scraping:")
        print(f"   Total documents: {docs_after}")
        print(f"   Scraped documents: {scraped_after}")
        print(f"   New documents: {docs_after - docs_before}")
        
        # Show metadata quality for recent documents
        print(f"\n🔍 Metadata Quality Check:")
        
        recent_docs = db.query(Document).filter(
            Document.source_url.isnot(None)
        ).order_by(Document.uploaded_at.desc()).limit(5).all()
        
        total_quality = 0
        doc_count = 0
        
        for i, doc in enumerate(recent_docs):
            metadata = db.query(DocumentMetadata).filter(
                DocumentMetadata.document_id == doc.id
            ).first()
            
            if metadata:
                # Calculate quality score
                score = 0
                if metadata.title and len(metadata.title) > 10: score += 1
                if metadata.department and metadata.department != "General": score += 1
                if metadata.document_type and metadata.document_type != "Uncategorized": score += 1
                if metadata.summary and len(metadata.summary) > 50: score += 1
                if metadata.metadata_status == 'ready': score += 1
                if doc.extracted_text and len(doc.extracted_text) > 100: score += 1
                
                quality_pct = (score / 6) * 100
                total_quality += quality_pct
                doc_count += 1
                
                print(f"   {i+1}. {doc.filename[:50]}...")
                print(f"      Quality: {score}/6 ({quality_pct:.1f}%)")
                print(f"      Title: {metadata.title[:40]}..." if metadata.title else "      Title: None")
                print(f"      Dept: {metadata.department or 'None'}")
                print(f"      Type: {metadata.document_type or 'None'}")
                print(f"      Summary: {len(metadata.summary or '')} chars")
        
        if doc_count > 0:
            avg_quality = total_quality / doc_count
            print(f"\n📊 Average Metadata Quality: {avg_quality:.1f}%")
        
        print(f"\n🎉 Test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_moe_scraping()