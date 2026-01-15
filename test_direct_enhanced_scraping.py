#!/usr/bin/env python3
"""
Direct test of enhanced scraping without API dependency
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_direct_enhanced_scraping():
    """Test enhanced scraping directly"""
    print("🧪 Direct Enhanced Scraping Test")
    print("=" * 50)
    
    try:
        from backend.database import SessionLocal, Document, DocumentMetadata, WebScrapingSource
        
        db = SessionLocal()
        
        # Check database connection
        print("✅ Database connection successful")
        
        # Check sources
        sources = db.query(WebScrapingSource).all()
        print(f"📋 Available sources: {len(sources)}")
        
        for source in sources:
            print(f"   {source.id}: {source.name}")
        
        # Count current documents
        total_docs = db.query(Document).count()
        scraped_docs = db.query(Document).filter(Document.source_url.isnot(None)).count()
        
        print(f"\n📊 Current database state:")
        print(f"   Total documents: {total_docs}")
        print(f"   Scraped documents: {scraped_docs}")
        
        # Test the enhanced processor import
        try:
            from Agent.web_scraping.enhanced_processor import enhanced_scrape_source
            print("✅ Enhanced processor imported successfully")
        except Exception as e:
            print(f"❌ Enhanced processor import failed: {e}")
            return
        
        # Test metadata extractor
        try:
            from Agent.metadata.extractor import MetadataExtractor
            extractor = MetadataExtractor()
            print("✅ Metadata extractor initialized")
        except Exception as e:
            print(f"❌ Metadata extractor failed: {e}")
            return
        
        # Test site scrapers
        try:
            from Agent.web_scraping.site_scrapers import get_scraper_for_site
            scraper = get_scraper_for_site("moe")
            print(f"✅ Site scraper loaded: {scraper.__class__.__name__}")
        except Exception as e:
            print(f"❌ Site scraper failed: {e}")
            return
        
        print(f"\n🎯 All components loaded successfully!")
        print(f"✅ Enhanced scraping system is ready")
        
        # Test a small scraping operation if user wants
        if len(sources) > 0:
            print(f"\n🚀 Testing small scraping operation...")
            
            # Use first available source
            source = sources[0]
            print(f"   Using source: {source.name}")
            
            try:
                result = enhanced_scrape_source(
                    source_id=source.id,
                    max_documents=1,  # Just 1 document for testing
                    pagination_enabled=False,
                    max_pages=1
                )
                
                print(f"\n✅ Scraping test completed!")
                print(f"   Status: {result.get('status')}")
                print(f"   Documents discovered: {result.get('documents_discovered', 0)}")
                print(f"   Documents new: {result.get('documents_new', 0)}")
                print(f"   Execution time: {result.get('execution_time', 0):.2f}s")
                
                # Check if any new documents were added
                new_total = db.query(Document).count()
                if new_total > total_docs:
                    print(f"   ✅ {new_total - total_docs} new document(s) added to database")
                    
                    # Check metadata of newest document
                    newest_doc = db.query(Document).order_by(Document.uploaded_at.desc()).first()
                    if newest_doc and newest_doc.source_url:
                        metadata = db.query(DocumentMetadata).filter(
                            DocumentMetadata.document_id == newest_doc.id
                        ).first()
                        
                        if metadata:
                            print(f"\n📋 Newest document metadata:")
                            print(f"      Title: {metadata.title[:60]}..." if metadata.title else "      Title: None")
                            print(f"      Department: {metadata.department or 'None'}")
                            print(f"      Type: {metadata.document_type or 'None'}")
                            print(f"      Summary: {len(metadata.summary or '')} chars")
                            print(f"      Status: {metadata.metadata_status}")
                else:
                    print(f"   ℹ️  No new documents added (may be duplicates)")
                
            except Exception as e:
                print(f"❌ Scraping test failed: {e}")
                import traceback
                traceback.print_exc()
        
        db.close()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_direct_enhanced_scraping()