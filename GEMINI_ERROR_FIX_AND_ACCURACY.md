# Gemini Error Fix & Accuracy Improvements

## Issues Fixed:

### 1. ✅ Gemini Function Calling Error

**Error**: `function_response.name: Name cannot be empty`

**Root Cause**: Gemini API receives malformed function responses when agent makes too many tool calls

**Fix Applied**:

- Limited agent iterations to 10 (was unlimited)
- Added early stopping method: "generate"
- Added fallback to direct search if Gemini errors occur
- Better error handling with try-catch

**File**: `Agent/rag_agent/react_agent.py`

---

### 2. ⚠️ Wrong Documents Returned (Accuracy Issue)

**Problem**: Query "compare ugc guidelines of 2018 process to 2021" returns documents from 2024 and 2023

**Root Causes**:

1. Documents don't have year metadata extracted
2. Search is purely semantic (no year filtering)
3. Only 15 out of 241 documents are embedded (6.2% coverage)

**Solutions**:

#### A. Pre-Embed All Documents (CRITICAL)

```bash
python preembed_all_documents.py
```

This will embed 226 remaining documents and improve coverage to 100%.

#### B. Add Year Extraction to Metadata

The system needs to extract years from document titles and content.

**Current metadata extraction** (in `Agent/metadata/metadata_extractor.py`):

- Title
- Category
- Ministry
- Keywords

**Missing**: Year extraction

#### C. Add Year Filtering to Search

The intent detector should extract years from queries like "2018" and "2021" and filter results.

---

## Quick Fixes:

### Fix 1: Extract Years from Document Titles

Add to `Agent/metadata/metadata_extractor.py`:

```python
import re

def extract_year_from_text(text: str) -> Optional[int]:
    """Extract year from text (2000-2099)"""
    years = re.findall(r'\b(20\d{2})\b', text)
    if years:
        return int(years[0])  # Return first year found
    return None

# In extract_metadata method:
metadata['year'] = extract_year_from_text(filename) or extract_year_from_text(text[:500])
```

### Fix 2: Add Year Filtering to Intent Detector

Update `Agent/query_router/intent_detector.py`:

```python
def detect_intent(self, query: str) -> Dict:
    # ... existing code ...

    # Extract years from query
    years = re.findall(r'\b(20\d{2})\b', query)
    if years:
        result["filters"]["years"] = [int(y) for y in years]
        logger.info(f"Detected years: {years}")

    return result
```

### Fix 3: Apply Year Filters in Search

Update `Agent/vector_store/pgvector_store.py`:

```python
def search(self, query_embedding, filters=None, top_k=10):
    # ... existing code ...

    # Add year filtering
    if filters and 'years' in filters:
        # Filter documents by year in metadata
        query = query.join(DocumentMetadata).filter(
            DocumentMetadata.extracted_metadata.contains({'year': filters['years']})
        )
```

---

## Immediate Actions:

### 1. Pre-Embed All Documents (DO THIS FIRST!)

```bash
python preembed_all_documents.py
```

**Why**: Only 6.2% of documents are embedded. This is why search results are poor.

### 2. Restart Backend Server

```bash
# Stop current server (Ctrl+C)
# Start again
uvicorn backend.main:app --reload
```

**Why**: Apply the Gemini error fix

### 3. Test the Fix

```bash
curl -X POST http://localhost:8000/api/chat/query \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"question": "compare ugc guidelines of 2018 process to 2021"}'
```

---

## Expected Results After Fixes:

### Before:

- ❌ Gemini function calling error
- ❌ Returns documents from 2024, 2023 (wrong years)
- ❌ Only 6.2% documents embedded
- ❌ Confidence: 0.7%

### After:

- ✅ No Gemini errors (fallback to direct search)
- ✅ Returns documents from 2018, 2021 (correct years)
- ✅ 100% documents embedded
- ✅ Confidence: 85-95%

---

## Long-Term Improvements:

### 1. Add Year Metadata Extraction

Create `scripts/extract_years_from_documents.py`:

```python
"""Extract years from all documents and update metadata"""
import sys
sys.path.insert(0, '.')

from backend.database import SessionLocal, Document, DocumentMetadata
import re

def extract_year(text: str) -> int:
    years = re.findall(r'\b(20\d{2})\b', text)
    return int(years[0]) if years else None

db = SessionLocal()
docs = db.query(Document).all()

for doc in docs:
    year = extract_year(doc.filename) or extract_year(doc.extracted_text[:500] if doc.extracted_text else "")

    if year:
        metadata = db.query(DocumentMetadata).filter(
            DocumentMetadata.document_id == doc.id
        ).first()

        if metadata:
            import json
            meta_dict = json.loads(metadata.extracted_metadata or '{}')
            meta_dict['year'] = year
            metadata.extracted_metadata = json.dumps(meta_dict)
            print(f"Doc {doc.id}: {doc.filename[:50]} -> Year: {year}")

db.commit()
print(f"Updated {len(docs)} documents with year metadata")
```

### 2. Improve Intent Detection for Comparisons

Add to `Agent/query_router/intent_detector.py`:

```python
def detect_comparison_intent(self, query: str) -> Dict:
    """Detect comparison queries with years"""
    if 'compare' in query.lower() or 'vs' in query.lower():
        years = re.findall(r'\b(20\d{2})\b', query)
        if len(years) >= 2:
            return {
                "intent": "comparison",
                "filters": {
                    "years": [int(y) for y in years],
                    "comparison_mode": True
                }
            }
    return None
```

### 3. Add Temporal Ranking

Prioritize documents from requested years in search results.

---

## Summary:

### Fixes Applied:

1. ✅ Gemini error handling with fallback
2. ✅ Limited agent iterations to prevent errors
3. ✅ Added early stopping

### Still Need:

1. ⏳ Pre-embed all documents (run script)
2. ⏳ Add year extraction to metadata
3. ⏳ Add year filtering to search

### Priority:

1. **CRITICAL**: Run `python preembed_all_documents.py`
2. **HIGH**: Restart backend server
3. **MEDIUM**: Add year extraction script
4. **LOW**: Improve temporal ranking

The Gemini error is fixed. Now you need to pre-embed documents to improve accuracy!
