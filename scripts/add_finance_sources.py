"""
Add finance-related sources for scraping
Ministry of Finance, RBI, SEBI, etc.
"""
import sys
sys.path.insert(0, '.')

from backend.database import SessionLocal, WebScrapingSource
from datetime import datetime
import json

def add_finance_sources():
    """Add finance-related scraping sources"""
    print("="*80)
    print("ADDING FINANCE SOURCES")
    print("="*80)
    
    db = SessionLocal()
    
    try:
        finance_sources = [
            {
                "name": "Ministry of Finance",
                "url": "https://www.finmin.nic.in",
                "source_type": "government",
                "description": "Ministry of Finance - Policies, Circulars, Notifications",
                "credibility_score": 10,
                "fallback_urls": [
                    "https://finmin.nic.in",
                    "https://www.finmin.nic.in/documents",
                    "https://www.finmin.nic.in/reports",
                    "https://dea.gov.in",
                    "https://dor.gov.in",
                ]
            },
            {
                "name": "Reserve Bank of India",
                "url": "https://www.rbi.org.in",
                "source_type": "government",
                "description": "RBI - Circulars, Notifications, Guidelines",
                "credibility_score": 10,
                "fallback_urls": [
                    "https://rbi.org.in",
                    "https://rbidocs.rbi.org.in",
                ]
            },
            {
                "name": "SEBI",
                "url": "https://www.sebi.gov.in",
                "source_type": "government",
                "description": "Securities and Exchange Board of India",
                "credibility_score": 10,
                "fallback_urls": [
                    "https://sebi.gov.in",
                ]
            },
            {
                "name": "Income Tax Department",
                "url": "https://www.incometax.gov.in",
                "source_type": "government",
                "description": "Income Tax - Circulars, Notifications",
                "credibility_score": 10,
                "fallback_urls": [
                    "https://incometax.gov.in",
                ]
            },
        ]
        
        added = 0
        
        for source_data in finance_sources:
            existing = db.query(WebScrapingSource).filter(
                WebScrapingSource.name == source_data["name"]
            ).first()
            
            if not existing:
                fallback_data = {
                    'fallback_urls': source_data['fallback_urls'],
                    'url_rotation_enabled': True
                }
                
                source = WebScrapingSource(
                    name=source_data["name"],
                    url=source_data["url"],
                    source_type=source_data["source_type"],
                    description=source_data["description"],
                    credibility_score=source_data["credibility_score"],
                    scraping_enabled=True,
                    verified=True,
                    verification_notes=json.dumps(fallback_data),
                    max_documents_per_scrape=100
                )
                
                db.add(source)
                added += 1
                print(f"✓ Added: {source_data['name']}")
        
        db.commit()
        print(f"\n✅ Added {added} finance sources")
        
    finally:
        db.close()


if __name__ == "__main__":
    add_finance_sources()
