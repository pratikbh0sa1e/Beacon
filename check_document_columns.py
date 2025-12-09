"""Check what columns exist in documents table"""
import sys
sys.path.insert(0, '.')

from backend.database import SessionLocal, Document
from sqlalchemy import inspect

db = SessionLocal()

try:
    # Get table columns
    inspector = inspect(db.bind)
    columns = inspector.get_columns('documents')
    
    print("="*80)
    print("DOCUMENTS TABLE COLUMNS")
    print("="*80)
    
    # Filter for version and date related columns
    version_date_cols = [col for col in columns if 'version' in col['name'].lower() or 'date' in col['name'].lower()]
    
    print("\nVersion/Date Related Columns:")
    for col in version_date_cols:
        print(f"  {col['name']}: {col['type']}")
    
    print("\nAll Columns:")
    for col in columns:
        print(f"  {col['name']}: {col['type']}")
    
    # Check if any documents have version_date populated
    print("\n" + "="*80)
    print("SAMPLE DOCUMENTS WITH VERSION INFO")
    print("="*80)
    
    docs = db.query(Document).limit(5).all()
    for doc in docs:
        print(f"\nDoc ID: {doc.id}")
        print(f"  Filename: {doc.filename[:60]}")
        
        # Check all version-related attributes
        for attr in dir(doc):
            if 'version' in attr.lower() and not attr.startswith('_'):
                value = getattr(doc, attr, None)
                if value is not None and not callable(value):
                    print(f"  {attr}: {value}")
        
        # Check date attributes
        for attr in ['uploaded_at', 'approved_at', 'escalated_at', 'expiry_date']:
            value = getattr(doc, attr, None)
            if value:
                print(f"  {attr}: {value}")

finally:
    db.close()
