#!/usr/bin/env python3
"""
Test Enhanced Scraping with Full Metadata Extraction
Test that enhanced scraping follows the same workflow as normal document uploads
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_enhanced_scraping_with_metadata():
    """Test enhanced scraping with complete metadata extraction"""
    print("🧪 Testing Enhanced Scraping with Full Metadata Extraction")
    print("=" * 70)
    
    try:
        from backend.database import SessionLocal, Document, DocumentMetadata
        from Agent.web_scraping.enhanced_processor import enhanced_scrape_source
        
        # Count documents and metadata before
        db = SessionLocal()
        
        try:
            docs_before = db.query(Document).count()
            metadata_before = db.query(DocumentMetadata).count()
            
            print(f"📊 Before enhanced scraping:")
            print(f"   Total documents: {docs_before}")
            print(f"   Total metadata records: {metadata_before}")
            
        finally:
            db.close()
        
        # Test enhanced scraping with metadata extraction
        print(f"\n🚀 Running enhanced scraping with metadata extraction...")
        
        result = enhanced_scrape_source(
            source_id=3,  # MoE source
            keywords=None,
            max_documents=2,  # Small number for testing
            pagination_enabled=False,
            max_pages=1,
            incremental=False
        )
        
        print(f"✅ Enhanced scraping completed!")
        print(f"📊 Results:")
        print(f"   Status: {result.get('status')}")
        print(f"   Execution time: {result.get('execution_time', 0):.2f}s")
        print(f"   Scraper used: {result.get('scraper_used', 'Unknown')}")
        print(f"   Documents discovered: {result.get('documents_discovered', 0)}")
        print(f"   Documents new: {result.get('documents_new', 0)}")
        print(f"   Documents processed: {result.get('documents_processed', 0)}")
        
        if result.get('errors'):
            print(f"   Errors: {len(result['errors'])}")
            for error in result['errors'][:2]:
                print(f"     - {error}")
        
        # Check documents and metadata after
        db = SessionLocal()
        
        try:
            docs_after = db.query(Document).count()
            metadata_after = db.query(DocumentMetadata).count()
            
            print(f"\n📊 After enhanced scraping:")
            print(f"   Total documents: {docs_after}")
            print(f"   Total metadata records: {metadata_after}")
            print(f"   New documents added: {docs_after - docs_before}")
            print(f"   New metadata records: {metadata_after - metadata_before}")
            
            # Show detailed metadata for new documents
            if docs_after > docs_before:
                print(f"\n📋 New documents with metadata:")
                new_docs = db.query(Document).filter(
                    Document.source_url.isnot(None)
                ).order_by(Document.uploaded_at.desc()).limit(3).all()
                
                for doc in new_docs:
                    print(f"\n   📄 Document ID: {doc.id}")
                    print(f"      Filename: {doc.filename}")
                    print(f"      URL: {doc.source_url}")
                    print(f"      File Type: {doc.file_type}")
                    print(f"      Text Length: {len(doc.extracted_text)} chars")
                    print(f"      Is Scanned: {doc.is_scanned}")
                    print(f"      Uploaded: {doc.uploaded_at}")
                    
                    # Get metadata
                    metadata = db.query(DocumentMetadata).filter(
                        DocumentMetadata.document_id == doc.id
                    ).first()
                    
                    if metadata:
                        print(f"      📊 Metadata:")
                        print(f"         Title: {metadata.title}")
                        print(f"         Department: {metadata.department}")
                        print(f"         Document Type: {metadata.document_type}")
                        print(f"         Summary: {metadata.summary[:100] if metadata.summary else 'None'}...")
                        print(f"         Keywords: {metadata.keywords[:5] if metadata.keywords else []}")
                        print(f"         Metadata Status: {metadata.metadata_status}")
                        print(f"         Embedding Status: {metadata.embedding_status}")
                    else:
                        print(f"      ❌ No metadata found")
            
        finally:
            db.close()
        
    except Exception as e:
        print(f"❌ Error in enhanced scraping test: {e}")
        import traceback
        traceback.print_exc()

def verify_metadata_quality():
    """Verify the quality of extracted metadata"""
    print("\n" + "=" * 70)
    print("🔍 Verifying Metadata Quality")
    print("=" * 70)
    
    try:
        from backend.database import SessionLocal, Document, DocumentMetadata
        
        db = SessionLocal()
        
        try:
            # Get recent scraped documents with metadata
            recent_docs = db.query(Document).filter(
                Document.source_url.isnot(None)
            ).order_by(Document.uploaded_at.desc()).limit(5).all()
            
            print(f"📊 Analyzing {len(recent_docs)} recent scraped documents:")
            
            for i, doc in enumerate(recent_docs):
                metadata = db.query(DocumentMetadata).filter(
                    DocumentMetadata.document_id == doc.id
                ).first()
                
                print(f"\n   {i+1}. Document: {doc.filename[:50]}...")
                
                if metadata:
                    # Check metadata completeness
                    completeness_score = 0
                    total_fields = 7
                    
                    if metadata.title and metadata.title != doc.filename:
                        completeness_score += 1
                        print(f"      ✅ Title: {metadata.title[:50]}...")
                    else:
                        print(f"      ⚠️  Title: Same as filename")
                    
                    if metadata.department and metadata.department != "General":
                        completeness_score += 1
                        print(f"      ✅ Department: {metadata.department}")
                    else:
                        print(f"      ⚠️  Department: {metadata.department or 'None'}")
                    
                    if metadata.document_type and metadata.document_type != "Uncategorized":
                        completeness_score += 1
                        print(f"      ✅ Document Type: {metadata.document_type}")
                    else:
                        print(f"      ⚠️  Document Type: {metadata.document_type or 'None'}")
                    
                    if metadata.summary and len(metadata.summary) > 20:
                        completeness_score += 1
                        print(f"      ✅ Summary: {len(metadata.summary)} chars")
                    else:
                        print(f"      ⚠️  Summary: {len(metadata.summary or '') if metadata.summary else 0} chars")
                    
                    if metadata.keywords and len(metadata.keywords) > 0:
                        completeness_score += 1
                        print(f"      ✅ Keywords: {len(metadata.keywords)} items")
                    else:
                        print(f"      ⚠️  Keywords: None")
                    
                    if metadata.metadata_status == 'ready':
                        completeness_score += 1
                        print(f"      ✅ Metadata Status: {metadata.metadata_status}")
                    else:
                        print(f"      ⚠️  Metadata Status: {metadata.metadata_status}")
                    
                    if doc.extracted_text and len(doc.extracted_text) > 100:
                        completeness_score += 1
                        print(f"      ✅ Extracted Text: {len(doc.extracted_text)} chars")
                    else:
                        print(f"      ⚠️  Extracted Text: {len(doc.extracted_text or '')} chars")
                    
                    quality_percentage = (completeness_score / total_fields) * 100
                    print(f"      📊 Quality Score: {completeness_score}/{total_fields} ({quality_percentage:.1f}%)")
                    
                else:
                    print(f"      ❌ No metadata record found")
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error verifying metadata: {e}")

def test_scraped_documents_api_with_metadata():
    """Test that the API returns documents with proper metadata"""
    print("\n" + "=" * 70)
    print("🌐 Testing Scraped Documents API with Metadata")
    print("=" * 70)
    
    try:
        import requests
        
        response = requests.get("http://localhost:8000/api/web-scraping/scraped-documents?limit=3")
        
        print(f"📡 API Status: {response.status_code}")
        
        if response.status_code == 200:
            docs = response.json()
            print(f"✅ Found {len(docs)} scraped documents in API")
            
            for i, doc in enumerate(docs):
                print(f"\n   {i+1}. API Document:")
                print(f"      Title: {doc.get('title', 'No title')}")
                print(f"      URL: {doc.get('url', 'No URL')}")
                print(f"      Source: {doc.get('source_name', 'Unknown')}")
                print(f"      Type: {doc.get('type', 'Unknown')}")
                print(f"      Scraped: {doc.get('scraped_at', 'Unknown')}")
                
                # Check if provenance data is available
                if 'provenance' in doc:
                    prov = doc['provenance']
                    print(f"      Credibility: {prov.get('credibility_score', 'N/A')}/10")
                    print(f"      Verified: {prov.get('verified', False)}")
        else:
            print(f"❌ API failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")

if __name__ == "__main__":
    test_enhanced_scraping_with_metadata()
    verify_metadata_quality()
    test_scraped_documents_api_with_metadata()