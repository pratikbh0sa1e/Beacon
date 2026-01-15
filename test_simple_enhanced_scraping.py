#!/usr/bin/env python3
"""
Simple test for enhanced scraping with metadata extraction
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database import SessionLocal, Document, DocumentMetadata, WebScrapingSource
from Agent.web_scraping.enhanced_processor import enhanced_scrape_source

def test_simple_enhanced_scraping():
    """Test enhanced scraping with a simple approach"""
    print("🧪 Simple Enhanced Scraping Test")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        # Check if we have any sources
        sources = db.query(WebScrapingSource).all()
        print(f"📋 Available sources: {len(sources)}")
        
        if not sources:
            print("❌ No web scraping sources found")
            return
        
        # Use the first source
        source = sources[0]
        print(f"🎯 Testing with source: {source.name}")
        print(f"   URL: {source.url}")
        
        # Count documents before
        docs_before = db.query(Document).count()
        scraped_docs_before = db.query(Document).filter(
            Document.source_url.isnot(None)
        ).count()
        
        print(f"\n📊 Before scraping:")
        print(f"   Total documents: {docs_before}")
        print(f"   Scraped documents: {scraped_docs_before}")
        
        # Run enhanced scraping with minimal parameters
        print(f"\n🚀 Running enhanced scraping...")
        
        try:
            result = enhanced_scrape_source(
                source_id=source.id,
                max_documents=3,  # Limit to 3 for testing
                pagination_enabled=False,
                max_pages=1
            )
            
            print(f"✅ Scraping completed!")
            print(f"   Status: {result.get('status')}")
            print(f"   Documents discovered: {result.get('documents_discovered', 0)}")
            print(f"   Documents new: {result.get('documents_new', 0)}")
            print(f"   Documents processed: {result.get('documents_processed', 0)}")
            print(f"   Execution time: {result.get('execution_time', 0):.2f}s")
            
            if result.get('errors'):
                print(f"   Errors: {len(result['errors'])}")
                for error in result['errors'][:3]:
                    print(f"     - {error}")
            
        except Exception as e:
            print(f"❌ Scraping failed: {e}")
            return
        
        # Count documents after
        docs_after = db.query(Document).count()
        scraped_docs_after = db.query(Document).filter(
            Document.source_url.isnot(None)
        ).count()
        
        print(f"\n📊 After scraping:")
        print(f"   Total documents: {docs_after}")
        print(f"   Scraped documents: {scraped_docs_after}")
        print(f"   New documents: {docs_after - docs_before}")
        
        # Check metadata quality for new documents
        if docs_after > docs_before:
            print(f"\n🔍 Checking metadata quality...")
            
            new_docs = db.query(Document).filter(
                Document.source_url.isnot(None)
            ).order_by(Document.uploaded_at.desc()).limit(3).all()
            
            for i, doc in enumerate(new_docs):
                print(f"\n   {i+1}. Document ID: {doc.id}")
                print(f"      Filename: {doc.filename}")
                print(f"      URL: {doc.source_url}")
                print(f"      Text length: {len(doc.extracted_text or '')} chars")
                
                # Check metadata
                metadata = db.query(DocumentMetadata).filter(
                    DocumentMetadata.document_id == doc.id
                ).first()
                
                if metadata:
                    print(f"      Title: {metadata.title or 'None'}")
                    print(f"      Department: {metadata.department or 'None'}")
                    print(f"      Document Type: {metadata.document_type or 'None'}")
                    print(f"      Summary: {len(metadata.summary or '')} chars")
                    print(f"      Keywords: {len(metadata.keywords or [])} items")
                    print(f"      Status: {metadata.metadata_status}")
                else:
                    print(f"      ❌ No metadata found")
        
    finally:
        db.close()

if __name__ == "__main__":
    test_simple_enhanced_scraping()