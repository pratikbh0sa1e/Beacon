# 🎯 Fix Year Filtering - Quick Start

## Problem:

Query "compare ugc guidelines of 2018 process to 2021" returns wrong documents (2024, 2023)

## Root Cause:

`version_date` column exists but is **NULL** for all documents

## ✅ Solution (3 Steps):

### Step 1: Populate version_date

```bash
python scripts/populate_version_dates.py
```

This will:

- Extract years from filenames (e.g., "UGC 2018.pdf" → 2018)
- Extract years from document content
- Use uploaded_at as fallback
- Set version_date to January 1st of that year

**Expected output:**

```
Doc 15: Notice for List of Institutions Approved... -> 2023 (from filename)
Doc 199: UGC letter regarding: 5th Anniversary... -> 2023 (from content)
...
Total updated: 241
Coverage: 100%
```

### Step 2: Restart Backend Server

```bash
# Stop current server (Ctrl+C)
# Start again:
uvicorn backend.main:app --reload
```

### Step 3: Test Year Filtering

```bash
# Test intent detector
python -c "
from Agent.query_router.intent_detector import IntentDetector
detector = IntentDetector()
result = detector.detect_intent('compare ugc guidelines of 2018 process to 2021')
print(result)
"
```

**Expected output:**

```python
{
  'intent': 'latest_version',
  'filters': {
    'is_latest_version': True,
    'ministry': 'ugc',
    'category': 'guideline',
    'years': [2018, 2021]  # ← Years extracted!
  },
  'query_type': 'rule_query',
  'detected_keywords': ['guideline', 'guidelines']
}
```

---

## What's Been Fixed:

### 1. ✅ Intent Detector

**File**: `Agent/query_router/intent_detector.py`

- Extracts years from queries: `[2018, 2021]`

### 2. ✅ PGVector Search

**File**: `Agent/vector_store/pgvector_store.py`

- Filters by year: `WHERE EXTRACT(year FROM version_date) IN (2018, 2021)`

### 3. ✅ Gemini Error

**File**: `Agent/rag_agent/react_agent.py`

- Added fallback for function calling errors
- Limited iterations to 10

### 4. ⏳ Version Date Population

**File**: `scripts/populate_version_dates.py`

- Ready to run!

---

## After Running Script:

### Database Before:

```sql
SELECT id, filename, version_date FROM documents LIMIT 3;
-- All version_date are NULL
```

### Database After:

```sql
SELECT id, filename, version_date FROM documents LIMIT 3;
-- 15  | Notice for List... | 2023-01-01
-- 199 | UGC letter...      | 2023-01-01
-- 10  | दूरभाष निर्देशिका  | 2025-01-01
```

### Query Results Before:

```
Query: "compare ugc guidelines of 2018 process to 2021"
Results:
  ❌ UGC Circular 2024 (wrong year)
  ❌ Monthly Summary 2023 (wrong year)
```

### Query Results After:

```
Query: "compare ugc guidelines of 2018 process to 2021"
Results:
  ✅ UGC Guidelines 2018 (correct!)
  ✅ UGC Guidelines 2021 (correct!)
```

---

## Complete Workflow:

```bash
# 1. Populate version dates
python scripts/populate_version_dates.py

# 2. Pre-embed all documents (if not done yet)
python preembed_all_documents.py

# 3. Restart backend
# Ctrl+C to stop, then:
uvicorn backend.main:app --reload

# 4. Test query
curl -X POST http://localhost:8000/api/chat/query \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"question": "compare ugc guidelines of 2018 process to 2021"}'
```

---

## Summary:

| Component       | Status     | Action                                         |
| --------------- | ---------- | ---------------------------------------------- |
| Intent Detector | ✅ Done    | Extracts years from queries                    |
| PGVector Search | ✅ Done    | Filters by year                                |
| Gemini Error    | ✅ Fixed   | Fallback added                                 |
| version_date    | ⏳ Pending | Run `python scripts/populate_version_dates.py` |
| Pre-embedding   | ⏳ Pending | Run `python preembed_all_documents.py`         |

**Next**: Run the two scripts above and restart the server!
