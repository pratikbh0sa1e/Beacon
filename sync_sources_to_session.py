"""
Sync database sources to session storage
So the frontend can see all sources
"""
from backend.database import SessionLocal, WebScrapingSource
from Agent.web_scraping.session_storage import SessionStorage
from datetime import datetime

def sync_sources():
    """Copy sources from database to session storage"""
    db = SessionLocal()
    session_storage = SessionStorage()
    
    # Get all sources from database
    db_sources = db.query(WebScrapingSource).all()
    
    # Load existing session sources
    session_sources = session_storage.load_sources()
    
    # Create a map of existing sources by name
    existing_names = {s['name'] for s in session_sources}
    
    # Add new sources
    added = 0
    for db_source in db_sources:
        if db_source.name not in existing_names:
            session_source = {
                "id": db_source.id,
                "name": db_source.name,
                "url": db_source.url,
                "description": db_source.description,
                "keywords": db_source.keywords or [],
                "max_documents": db_source.max_documents_per_scrape or 1000,
                "scraping_enabled": db_source.scraping_enabled,
                "last_scraped_at": db_source.last_scraped_at.isoformat() if db_source.last_scraped_at else None,
                "last_scrape_status": db_source.last_scrape_status,
                "total_documents_scraped": db_source.total_documents_scraped,
                "created_at": datetime.utcnow().isoformat()
            }
            session_sources.append(session_source)
            added += 1
            print(f"✅ Added: {db_source.name}")
    
    # Save back to session storage
    session_storage.save_sources(session_sources)
    
    db.close()
    
    print(f"\n{'='*60}")
    print(f"Sync Complete!")
    print(f"  ✅ Added {added} sources to session storage")
    print(f"  📊 Total sources in session: {len(session_sources)}")
    print(f"{'='*60}")
    print(f"\n🔄 Refresh your frontend to see all sources!")

if __name__ == "__main__":
    print("="*60)
    print("Syncing Database Sources to Session Storage")
    print("="*60)
    print()
    sync_sources()
