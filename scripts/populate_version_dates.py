"""
Extract years from document filenames/content and populate version_date field
"""
import sys
sys.path.insert(0, '.')

from backend.database import SessionLocal, Document
import re
from datetime import date

def extract_year_from_text(text: str) -> int:
    """Extract year (2000-2099) from text"""
    if not text:
        return None
    
    # Find all 4-digit years
    years = re.findall(r'\b(20\d{2})\b', text)
    
    if years:
        # Return the first year found
        return int(years[0])
    
    return None


def populate_version_dates():
    """Populate version_date for all documents"""
    print("="*80)
    print("POPULATING VERSION DATES")
    print("="*80)
    
    db = SessionLocal()
    
    try:
        # Get all documents
        docs = db.query(Document).all()
        
        print(f"\nTotal documents: {len(docs)}")
        
        updated_from_filename = 0
        updated_from_content = 0
        updated_from_uploaded = 0
        no_year_found = 0
        
        for doc in docs:
            year = None
            source = None
            
            # Strategy 1: Extract from filename
            year = extract_year_from_text(doc.filename)
            if year:
                source = "filename"
                updated_from_filename += 1
            
            # Strategy 2: Extract from document content (first 2000 chars)
            if not year and doc.extracted_text:
                year = extract_year_from_text(doc.extracted_text[:2000])
                if year:
                    source = "content"
                    updated_from_content += 1
            
            # Strategy 3: Use uploaded_at year as fallback
            if not year and doc.uploaded_at:
                year = doc.uploaded_at.year
                source = "uploaded_at"
                updated_from_uploaded += 1
            
            # Update version_date
            if year:
                doc.version_date = date(year, 1, 1)
                print(f"Doc {doc.id}: {doc.filename[:50]}... -> {year} (from {source})")
            else:
                no_year_found += 1
                print(f"Doc {doc.id}: {doc.filename[:50]}... -> No year found")
        
        # Commit changes
        db.commit()
        
        # Summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"\nTotal documents: {len(docs)}")
        print(f"  ✓ From filename: {updated_from_filename}")
        print(f"  ✓ From content: {updated_from_content}")
        print(f"  ✓ From uploaded_at: {updated_from_uploaded}")
        print(f"  ✗ No year found: {no_year_found}")
        print(f"\nTotal updated: {updated_from_filename + updated_from_content + updated_from_uploaded}")
        
        # Verify
        print("\n" + "="*80)
        print("VERIFICATION")
        print("="*80)
        
        docs_with_version_date = db.query(Document).filter(
            Document.version_date.isnot(None)
        ).count()
        
        print(f"\nDocuments with version_date: {docs_with_version_date}/{len(docs)}")
        print(f"Coverage: {docs_with_version_date/len(docs)*100:.1f}%")
        
        # Show sample
        print("\nSample documents with version_date:")
        sample_docs = db.query(Document).filter(
            Document.version_date.isnot(None)
        ).limit(10).all()
        
        for doc in sample_docs:
            print(f"  {doc.id}: {doc.filename[:50]}... -> {doc.version_date}")
        
        print("\n" + "="*80)
        print("✅ VERSION DATES POPULATED")
        print("="*80)
        
    finally:
        db.close()


if __name__ == "__main__":
    populate_version_dates()
