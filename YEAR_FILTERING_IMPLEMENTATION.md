# Year Filtering Implementation Summary

## ✅ What's Been Done:

### 1. Intent Detector Updated

**File**: `Agent/query_router/intent_detector.py`

Now extracts years from queries:

```python
# Query: "compare ugc guidelines of 2018 process to 2021"
result = detector.detect_intent(query)
# Returns: {"filters": {"years": [2018, 2021]}}
```

### 2. PGVector Search Updated

**File**: `Agent/vector_store/pgvector_store.py`

Added year filtering:

```python
def search(..., filters=None):
    # If filters contain years, join with Document table
    # and filter by extract('year', Document.version_date)
```

### 3. Database Schema Confirmed

**Table**: `documents`

Columns exist:

- `version_date` (DATE) - ✅ Exists but NOT populated
- `version_number` (NUMERIC) - ✅ Exists
- `is_latest_version` (BOOLEAN) - ✅ Exists
- `document_family_id` (INTEGER) - ✅ Exists

## ⚠️ Current Problem:

**`version_date` is NULL for all documents!**

Check:

```bash
python check_document_columns.py
```

Output shows:

```
Doc ID: 15
  version: 1.0
  uploaded_at: 2025-12-09 02:19:50.945103
  # version_date: NULL (not shown because it's NULL)
```

## 🔧 Solution: Populate version_date

### Option 1: Extract from Filename

Create `scripts/populate_version_dates.py`:

```python
"""
Extract years from document filenames and populate version_date
"""
import sys
sys.path.insert(0, '.')

from backend.database import SessionLocal, Document
import re
from datetime import date

def extract_year_from_text(text: str) -> int:
    """Extract year (2000-2099) from text"""
    years = re.findall(r'\b(20\d{2})\b', text)
    return int(years[0]) if years else None

db = SessionLocal()

try:
    docs = db.query(Document).all()
    updated = 0

    for doc in docs:
        # Try filename first
        year = extract_year_from_text(doc.filename)

        # Try extracted text if filename doesn't have year
        if not year and doc.extracted_text:
            year = extract_year_from_text(doc.extracted_text[:1000])

        if year:
            # Set version_date to January 1st of that year
            doc.version_date = date(year, 1, 1)
            updated += 1
            print(f"Doc {doc.id}: {doc.filename[:50]} -> {year}")

    db.commit()
    print(f"\n✅ Updated {updated}/{len(docs)} documents with version_date")

finally:
    db.close()
```

### Option 2: Extract from Document Content

Use NLP to extract dates from document text:

```python
from dateutil import parser

def extract_date_from_content(text: str):
    # Look for patterns like "dated 15-03-2018"
    date_patterns = [
        r'dated?\s+(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
        r'(\d{1,2}\s+\w+\s+\d{4})',  # 15 March 2018
    ]

    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            try:
                return parser.parse(matches[0])
            except:
                pass
    return None
```

### Option 3: Use uploaded_at as fallback

```python
# If no year found, use uploaded_at
if not doc.version_date and doc.uploaded_at:
    doc.version_date = doc.uploaded_at.date()
```

## 🚀 Quick Fix Script

```bash
# Create and run the script
python scripts/populate_version_dates.py
```

This will:

1. Extract years from filenames (e.g., "UGC Guidelines 2018.pdf" → 2018)
2. Extract years from document content if filename doesn't have it
3. Set version_date to January 1st of that year
4. Update database

## 📊 Expected Results After Fix:

### Before:

```sql
SELECT id, filename, version_date FROM documents LIMIT 5;
-- All version_date are NULL
```

### After:

```sql
SELECT id, filename, version_date FROM documents LIMIT 5;
-- version_date populated:
-- 1 | UGC Guidelines 2018.pdf | 2018-01-01
-- 2 | AICTE Rules 2021.pdf | 2021-01-01
```

### Query Results:

```
Query: "compare ugc guidelines of 2018 process to 2021"

Intent Detector:
  filters: {"years": [2018, 2021]}

PGVector Search:
  WHERE EXTRACT(year FROM version_date) IN (2018, 2021)

Results:
  ✅ UGC Guidelines 2018.pdf (version_date: 2018-01-01)
  ✅ UGC Guidelines 2021.pdf (version_date: 2021-01-01)
  ❌ UGC Guidelines 2024.pdf (filtered out)
```

## 🎯 Integration with RAG Agent

The RAG agent needs to use intent detector:

```python
# In Agent/rag_agent/react_agent.py

def query(self, question: str, ...):
    # Detect intent and extract filters
    from Agent.query_router.intent_detector import get_intent_detector
    detector = get_intent_detector()
    intent_result = detector.detect_intent(question)

    # Pass filters to search
    filters = intent_result['filters']

    # Search with filters
    results = self.pgvector_store.search(
        query_embedding=embedding,
        filters=filters,  # <-- Pass year filters here
        user_role=user_role,
        user_institution_id=user_institution_id
    )
```

## ✅ Summary:

1. **Intent Detector**: ✅ Extracts years from queries
2. **PGVector Search**: ✅ Filters by year when provided
3. **Database Schema**: ✅ Has version_date column
4. **Data Population**: ⏳ Need to run script to populate version_date
5. **RAG Integration**: ⏳ Need to connect intent detector to RAG agent

## 🔥 Next Steps:

1. Create `scripts/populate_version_dates.py`
2. Run it to populate version_date for all documents
3. Integrate intent detector into RAG agent
4. Test with: "compare ugc guidelines of 2018 process to 2021"

The infrastructure is ready! Just need to populate the data and connect the pieces.
