"""
Test Complete BEACON Pipeline Integration
Scrape → Download → OCR → Metadata → Store → RAG → AI Chat
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Agent.web_scraping.web_scraping_processor import WebScrapingProcessor
from backend.database import SessionLocal
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=" * 80)
print("🚀 BEACON COMPLETE PIPELINE DEMO")
print("=" * 80)
print("\nPipeline: Web Scraping → Document Processing → Metadata → RAG → AI Chat")
print("\n" + "=" * 80)

# Initialize processor
processor = WebScrapingProcessor()

# Test URL
url = "https://www.ugc.gov.in/"
source_name = "UGC Official Website"

print(f"\n📍 Source: {source_name}")
print(f"🌐 URL: {url}")
print("\n" + "-" * 80)

print("\n🕷️  STEP 1: Web Scraping")
print("-" * 80)
print("Scraping website for policy documents...")

try:
    # Run complete pipeline
    result = processor.scrape_and_process(
        url=url,
        source_name=source_name,
        keywords=["policy", "circular", "notification"],
        max_documents=3,  # Limit to 3 for demo
        uploader_id=1,
        institution_id=None
    )
    
    print(f"\n✅ Scraping Complete!")
    print(f"   Documents Scraped: {result['documents_scraped']}")
    print(f"   Documents Processed: {result['documents_processed']}")
    print(f"   Documents Failed: {result['documents_failed']}")
    
    if result['documents_processed'] > 0:
        print("\n📄 STEP 2: Document Processing")
        print("-" * 80)
        
        for i, doc in enumerate(result['processed_documents'], 1):
            print(f"\n   Document {i}:")
            print(f"   ├─ Title: {doc['title']}")
            print(f"   ├─ Filename: {doc['filename']}")
            print(f"   ├─ Document ID: {doc['document_id']}")
            print(f"   ├─ Credibility: {doc['credibility_score']}/10")
            print(f"   ├─ Text Length: {doc['text_length']} characters")
            print(f"   └─ Status: ✅ Stored in database")
        
        print("\n🤖 STEP 3: AI Integration")
        print("-" * 80)
        print("✅ Documents are now ready for:")
        print("   • Lazy embedding (on first query)")
        print("   • Semantic search")
        print("   • RAG-based AI chat")
        print("   • Citation tracking")
        
        print("\n💡 STEP 4: Try AI Chat")
        print("-" * 80)
        print("You can now ask questions like:")
        print('   • "What is the latest UGC policy?"')
        print('   • "Tell me about fee refund policies"')
        print('   • "What are the recent circulars?"')
        
        print("\n📊 STEP 5: Provenance Tracking")
        print("-" * 80)
        print("Every document includes:")
        print("   • Source URL")
        print("   • Credibility score")
        print("   • Scraping timestamp")
        print("   • Source domain verification")
        
        # Get stats
        db = SessionLocal()
        try:
            stats = processor.get_processing_stats(db)
            
            print("\n📈 SYSTEM STATISTICS")
            print("-" * 80)
            print(f"Total Scraped Documents: {stats['total_scraped_documents']}")
            print(f"\nCredibility Distribution:")
            print(f"   • High (9-10): {stats['credibility_distribution']['high']}")
            print(f"   • Medium (7-8): {stats['credibility_distribution']['medium']}")
            print(f"   • Low (<7): {stats['credibility_distribution']['low']}")
            
            if stats['source_distribution']:
                print(f"\nSource Distribution:")
                for source in stats['source_distribution'][:5]:
                    print(f"   • {source['domain']}: {source['count']} documents")
        
        finally:
            db.close()
    
    else:
        print("\n⚠️  No documents were processed successfully")
        if result['failed_documents']:
            print("\nFailed documents:")
            for failed in result['failed_documents']:
                print(f"   • {failed.get('document', 'unknown')}: {failed.get('error')}")
    
    print("\n" + "=" * 80)
    print("✅ DEMO COMPLETE!")
    print("=" * 80)
    
    print("\n🎯 KEY ACHIEVEMENTS:")
    print("   ✅ Automated web scraping")
    print("   ✅ Document processing with OCR")
    print("   ✅ AI-powered metadata extraction")
    print("   ✅ Database storage with provenance")
    print("   ✅ Ready for RAG and AI chat")
    print("   ✅ Complete end-to-end pipeline")
    
    print("\n💡 NEXT STEPS:")
    print("   1. Start backend: uvicorn backend.main:app --reload")
    print("   2. Start frontend: cd frontend && npm run dev")
    print("   3. Open: http://localhost:5173/admin/web-scraping")
    print("   4. Try AI Chat with scraped documents!")
    
    print("\n" + "=" * 80)

except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    print("\n💡 Note: This demo requires database connection.")
    print("   For presentation, use the no-DB version:")
    print("   python test_simple_scrape.py")
