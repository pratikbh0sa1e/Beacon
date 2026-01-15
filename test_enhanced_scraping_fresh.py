#!/usr/bin/env python3
"""
Fresh test for enhanced scraping with metadata extraction
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database import SessionLocal, Document, DocumentMetadata, WebScrapingSource
from Agent.web_scraping.enhanced_processor import enhanced_scrape_source

def test_enhanced_scraping_fresh():
    """Test enhanced scraping with fresh approach"""
    print("🧪 Fresh Enhanced Scraping Test")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Check available sources
        sources = db.query(WebScrapingSource).all()
        print(f"📋 Available sources: {len(sources)}")
        
        for source in sources:
            print(f"   {source.id}: {source.name} - {source.url}")
        
        if not sources:
            print("❌ No sources available")
            return
        
        # Use UGC source (ID 3) for testing
        source_id = 3
        source = db.query(WebScrapingSource).filter(WebScrapingSource.id == source_id).first()
        
        if not source:
            print(f"❌ Source {source_id} not found")
            return
        
        print(f"\n🎯 Testing with: {source.name}")
        print(f"   URL: {source.url}")
        
        # Count documents before
        docs_before = db.query(Document).count()
        scraped_before = db.query(Document).filter(Document.source_url.isnot(None)).count()
        
        print(f"\n📊 Before scraping:")
        print(f"   Total documents: {docs_before}")
        print(f"   Scraped documents: {scraped_before}")
        
        # Run enhanced scraping
        print(f"\n🚀 Starting enhanced scraping...")
        
        result = enhanced_scrape_source(
            source_id=source_id,
            max_documents=2,  # Limit to 2 for quick test
            pagination_enabled=False,
            max_pages=1
        )
        
        print(f"\n✅ Scraping Results:")
        print(f"   Status: {result.get('status')}")
        print(f"   Documents discovered: {result.get('documents_discovered', 0)}")
        print(f"   Documents new: {result.get('documents_new', 0)}")
        print(f"   Documents processed: {result.get('documents_processed', 0)}")
        print(f"   Execution time: {result.get('execution_time', 0):.2f}s")
        
        if result.get('errors'):
            print(f"   Errors: {len(result['errors'])}")
            for error in result['errors'][:2]:
                print(f"     - {error}")
        
        # Count documents after
        docs_after = db.query(Document).count()
        scraped_after = db.query(Document).filter(Document.source_url.isnot(None)).count()
        
        print(f"\n📊 After scraping:")
        print(f"   Total documents: {docs_after}")
        print(f"   Scraped documents: {scraped_after}")
        print(f"   New documents: {docs_after - docs_before}")
        
        # Check metadata for new documents
        if docs_after > docs_before:
            print(f"\n🔍 Checking new documents metadata:")
            
            new_docs = db.query(Document).filter(
                Document.source_url.isnot(None)
            ).order_by(Document.uploaded_at.desc()).limit(2).all()
            
            for i, doc in enumerate(new_docs):
                print(f"\n   📄 Document {i+1}:")
                print(f"      ID: {doc.id}")
                print(f"      Filename: {doc.filename[:80]}...")
                print(f"      URL: {doc.source_url}")
                print(f"      Text length: {len(doc.extracted_text or '')} chars")
                
                # Check metadata
                metadata = db.query(DocumentMetadata).filter(
                    DocumentMetadata.document_id == doc.id
                ).first()
                
                if metadata:
                    print(f"      📋 Metadata:")
                    print(f"         Title: {metadata.title[:60]}..." if metadata.title else "         Title: None")
                    print(f"         Department: {metadata.department or 'None'}")
                    print(f"         Type: {metadata.document_type or 'None'}")
                    print(f"         Summary: {len(metadata.summary or '')} chars")
                    print(f"         Keywords: {len(metadata.keywords or [])} items")
                    print(f"         Status: {metadata.metadata_status}")
                    
                    # Calculate quality score
                    score = 0
                    if metadata.title and metadata.title != doc.filename: score += 1
                    if metadata.department and metadata.department != "General": score += 1
                    if metadata.document_type and metadata.document_type != "Uncategorized": score += 1
                    if metadata.summary and len(metadata.summary) > 50: score += 1
                    if metadata.keywords and len(metadata.keywords) > 0: score += 1
                    if metadata.metadata_status == 'ready': score += 1
                    if doc.extracted_text and len(doc.extracted_text) > 100: score += 1
                    
                    print(f"         Quality: {score}/7 ({(score/7)*100:.1f}%)")
                else:
                    print(f"      ❌ No metadata found")
        
        print(f"\n🎉 Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_enhanced_scraping_fresh()