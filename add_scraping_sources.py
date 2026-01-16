"""
Add additional web scraping sources to the database
Run this to add UGC, AICTE, and other government sources
"""
from backend.database import SessionLocal, WebScrapingSource
from datetime import datetime

def add_scraping_sources():
    """Add common Indian government education sources"""
    db = SessionLocal()
    
    sources = [
        {
            "name": "University Grants Commission (UGC)",
            "url": "https://www.ugc.gov.in/page/Notices.aspx",
            "description": "UGC notices, circulars, and policy documents",
            "source_type": "government",
            "credibility_score": 10,
            "scraping_enabled": True,
            "scraping_frequency": "daily",
            "keywords": ["notice", "circular", "policy", "regulation", "guideline"],
            "max_documents_per_scrape": 1000,
            "pagination_enabled": True,
            "max_pages": 50
        },
        {
            "name": "All India Council for Technical Education (AICTE)",
            "url": "https://www.aicte-india.org/bureaus/approvals",
            "description": "AICTE approvals, regulations, and technical education policies",
            "source_type": "government",
            "credibility_score": 10,
            "scraping_enabled": True,
            "scraping_frequency": "weekly",
            "keywords": ["approval", "regulation", "technical", "engineering", "policy"],
            "max_documents_per_scrape": 500,
            "pagination_enabled": True,
            "max_pages": 30
        },
        {
            "name": "National Council for Teacher Education (NCTE)",
            "url": "https://ncte.gov.in/website/notifications.aspx",
            "description": "NCTE notifications and teacher education policies",
            "source_type": "government",
            "credibility_score": 9,
            "scraping_enabled": True,
            "scraping_frequency": "weekly",
            "keywords": ["notification", "teacher", "education", "training"],
            "max_documents_per_scrape": 300,
            "pagination_enabled": True,
            "max_pages": 20
        },
        {
            "name": "Ministry of Human Resource Development (MHRD)",
            "url": "https://www.education.gov.in/documents-reports",
            "description": "MHRD documents, reports, and policy papers",
            "source_type": "government",
            "credibility_score": 10,
            "scraping_enabled": True,
            "scraping_frequency": "daily",
            "keywords": ["document", "report", "policy", "education", "scheme"],
            "max_documents_per_scrape": 1000,
            "pagination_enabled": True,
            "max_pages": 50
        },
        {
            "name": "National Assessment and Accreditation Council (NAAC)",
            "url": "https://www.naac.gov.in/index.php/en/",
            "description": "NAAC accreditation guidelines and quality assurance documents",
            "source_type": "government",
            "credibility_score": 9,
            "scraping_enabled": True,
            "scraping_frequency": "monthly",
            "keywords": ["accreditation", "quality", "assessment", "guideline"],
            "max_documents_per_scrape": 200,
            "pagination_enabled": True,
            "max_pages": 15
        },
        {
            "name": "National Board of Accreditation (NBA)",
            "url": "https://www.nbaind.org/",
            "description": "NBA accreditation criteria and technical education standards",
            "source_type": "government",
            "credibility_score": 9,
            "scraping_enabled": True,
            "scraping_frequency": "monthly",
            "keywords": ["accreditation", "technical", "engineering", "standard"],
            "max_documents_per_scrape": 200,
            "pagination_enabled": True,
            "max_pages": 15
        },
        {
            "name": "Central Board of Secondary Education (CBSE)",
            "url": "https://www.cbse.gov.in/cbsenew/circulars.html",
            "description": "CBSE circulars, notifications, and academic policies",
            "source_type": "government",
            "credibility_score": 9,
            "scraping_enabled": True,
            "scraping_frequency": "daily",
            "keywords": ["circular", "notification", "academic", "examination"],
            "max_documents_per_scrape": 500,
            "pagination_enabled": True,
            "max_pages": 30
        },
        {
            "name": "National Institute of Educational Planning and Administration (NIEPA)",
            "url": "https://niepa.ac.in/publications.html",
            "description": "NIEPA research publications and educational planning documents",
            "source_type": "academic",
            "credibility_score": 8,
            "scraping_enabled": True,
            "scraping_frequency": "monthly",
            "keywords": ["research", "publication", "planning", "policy"],
            "max_documents_per_scrape": 200,
            "pagination_enabled": True,
            "max_pages": 20
        }
    ]
    
    added_count = 0
    skipped_count = 0
    
    for source_data in sources:
        # Check if source already exists
        existing = db.query(WebScrapingSource).filter(
            WebScrapingSource.name == source_data["name"]
        ).first()
        
        if existing:
            print(f"⚠️  Skipped: {source_data['name']} (already exists)")
            skipped_count += 1
            continue
        
        # Create new source
        source = WebScrapingSource(**source_data)
        db.add(source)
        print(f"✅ Added: {source_data['name']}")
        added_count += 1
    
    db.commit()
    db.close()
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  ✅ Added: {added_count} sources")
    print(f"  ⚠️  Skipped: {skipped_count} sources (already exist)")
    print(f"  📊 Total: {added_count + skipped_count} sources processed")
    print(f"{'='*60}")
    print(f"\n🚀 Scraping sources ready!")
    print(f"Go to Enhanced Web Scraping page to see all sources.")

if __name__ == "__main__":
    print("="*60)
    print("Adding Web Scraping Sources")
    print("="*60)
    print()
    add_scraping_sources()
