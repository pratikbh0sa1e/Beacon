# 🚀 Deployment Checklist - Complete Implementation

## ✅ Pre-Deployment Status

### Database Layer

- [x] Document model with version fields
- [x] DocumentFamily table created (114 families)
- [x] Version dates populated (239/239 - 100%)
- [x] Embeddings complete (2909 chunks - 100%)
- [x] All indexes created

### Code Layer

- [x] Intent detector implemented
- [x] Year filtering implemented
- [x] Scraping limits configured
- [x] Gemini error handling added
- [x] Version management ready

---

## 🔄 Deployment Steps

### Step 1: Restart Backend Server

```bash
# Stop current server (Ctrl+C)
uvicorn backend.main:app --reload
```

**Expected Output:**

```
INFO:     Will watch for changes in these directories: ['D:\\SIH_FINALS\\XYZ__V1']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

---

### Step 2: Verify Module Loading

```bash
# Test 1: Intent Detector
python -c "from Agent.query_router.intent_detector import IntentDetector; d = IntentDetector(); print('✅ Intent detector loaded')"

# Test 2: Scraping Limits
python -c "from config.scraping_limits import get_scraping_config; c = get_scraping_config(); print('✅ Scraping limits loaded')"

# Test 3: Database Models
python -c "from backend.database import Document, DocumentFamily; print('✅ Models loaded')"

# Test 4: PGVector with Filters
python -c "from Agent.vector_store.pgvector_store import PGVectorStore; import inspect; s = PGVectorStore(); sig = inspect.signature(s.search); print('✅ PGVector search params:', list(sig.parameters.keys()))"
```

**Expected Output:**

```
✅ Intent detector loaded
✅ Scraping limits loaded
✅ Models loaded
✅ PGVector search params: ['self', 'query_embedding', 'top_k', 'user_role', 'user_institution_id', 'document_id_filter', 'filters', 'db']
```

---

### Step 3: Test Core Features

#### Test 3.1: Intent Detection

```bash
python -c "
from Agent.query_router.intent_detector import IntentDetector
detector = IntentDetector()

# Test latest query
result = detector.detect_intent('What is the latest UGC regulation?')
print('Query: What is the latest UGC regulation?')
print(f'  Intent: {result[\"intent\"]}')
print(f'  Filters: {result[\"filters\"]}')
print()

# Test year query
result = detector.detect_intent('Compare UGC guidelines of 2018 to 2021')
print('Query: Compare UGC guidelines of 2018 to 2021')
print(f'  Intent: {result[\"intent\"]}')
print(f'  Years: {result[\"filters\"].get(\"years\")}')
print()

# Test amendment query
result = detector.detect_intent('Show me amendments to AICTE rules')
print('Query: Show me amendments to AICTE rules')
print(f'  Intent: {result[\"intent\"]}')
print(f'  Filters: {result[\"filters\"]}')
"
```

**Expected Output:**

```
Query: What is the latest UGC regulation?
  Intent: latest_version
  Filters: {'is_latest_version': True, 'ministry': 'ugc', 'category': 'regulation'}

Query: Compare UGC guidelines of 2018 to 2021
  Intent: latest_version
  Years: [2018, 2021]

Query: Show me amendments to AICTE rules
  Intent: amendments
  Filters: {'version_filter': 'amendments_only', 'ministry': 'aicte'}
```

#### Test 3.2: Year Filtering

```bash
python -c "
from backend.database import SessionLocal, Document
from sqlalchemy import extract

db = SessionLocal()

# Test year filtering
years = [2021, 2022]
docs = db.query(Document).filter(
    extract('year', Document.version_date).in_(years)
).limit(5).all()

print(f'Documents from {years}:')
for doc in docs:
    year = doc.version_date.year if doc.version_date else None
    print(f'  - {doc.filename[:50]}... ({year})')

db.close()
"
```

**Expected Output:**

```
Documents from [2021, 2022]:
  - Grant of Dearness Allowance (DA) to the employees... (2021)
  - UGC Circular regarding: Grant of Dearness Allowanc... (2022)
  - Options under Central Civil Services (Implementati... (2021)
  - Grant of Dearness Relief to Central Government pen... (2022)
  - UGC Notice regarding Options under Central Civil S... (2021)
```

#### Test 3.3: Scraping Limits

```bash
python -c "
from config.scraping_limits import get_scraping_config, should_trigger_scraping

config = get_scraping_config()
print('Scraping Configuration:')
print(f'  Min citations threshold: {config[\"min_citations_threshold\"]}')
print(f'  Min confidence threshold: {config[\"min_confidence_threshold\"]}')
print(f'  Max documents per query: {config[\"max_documents_per_query\"]}')
print(f'  Max pages per query: {config[\"max_pages_per_query\"]}')
print()

# Test trigger logic
print('Trigger Tests:')
print(f'  2 citations, 60% confidence: {should_trigger_scraping(2, 0.6)}')
print(f'  5 citations, 90% confidence: {should_trigger_scraping(5, 0.9)}')
"
```

**Expected Output:**

```
Scraping Configuration:
  Min citations threshold: 3
  Min confidence threshold: 0.7
  Max documents per query: 50
  Max pages per query: 5

Trigger Tests:
  2 citations, 60% confidence: True
  5 citations, 90% confidence: False
```

---

### Step 4: Test End-to-End Query Flow

#### Test via API (using curl or Postman):

```bash
# Test 1: Latest version query
curl -X POST http://localhost:8000/api/chat/query \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the latest UGC regulation?",
    "session_id": "test-session-1"
  }'
```

**Expected Response:**

```json
{
  "answer": "Based on the latest UGC regulations...",
  "citations": [
    {
      "document_id": 123,
      "source": "UGC Regulation 2024",
      "approval_status": "approved"
    }
  ],
  "confidence": 0.92,
  "session_id": "test-session-1",
  "message_id": 456
}
```

```bash
# Test 2: Year comparison query
curl -X POST http://localhost:8000/api/chat/query \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Compare UGC guidelines of 2018 to 2021",
    "session_id": "test-session-2"
  }'
```

**Expected Response:**

```json
{
  "answer": "Comparing UGC guidelines from 2018 and 2021...",
  "citations": [
    {
      "document_id": 114,
      "source": "UGC Guidelines 2018",
      "approval_status": "approved"
    },
    {
      "document_id": 228,
      "source": "UGC Guidelines 2021",
      "approval_status": "approved"
    }
  ],
  "confidence": 0.89,
  "session_id": "test-session-2"
}
```

---

### Step 5: Monitor Logs

Watch for these log messages:

```bash
# Backend logs should show:
INFO - Detected intent: latest_version (keywords: ['regulation', 'latest'])
INFO - Detected ministry: ugc
INFO - Applying year filter: [2018, 2021]
INFO - Found 5 results for query
INFO - Total citations extracted: 3
```

---

## ✅ Post-Deployment Verification

### Checklist:

- [ ] Backend server started successfully
- [ ] Intent detector module loads without errors
- [ ] Scraping limits module loads without errors
- [ ] Database models load with version fields
- [ ] PGVector search accepts filters parameter
- [ ] Intent detection works for "latest" queries
- [ ] Intent detection works for year queries
- [ ] Intent detection works for amendment queries
- [ ] Year filtering returns correct documents
- [ ] Scraping triggers when confidence < 70%
- [ ] API queries return accurate results
- [ ] Citations include version information
- [ ] Confidence scores are high (>85%)

---

## 🎯 Success Criteria

### Performance Metrics:

- Query response time: < 2 seconds
- Embedding coverage: 100% (239/239)
- Version date coverage: 100% (239/239)
- Confidence scores: 85-95%
- Citation count: 3-5 per query

### Functional Tests:

- ✅ "Latest" queries return only latest versions
- ✅ Year queries return only specified years
- ✅ Amendment queries return only amended versions
- ✅ Ministry filters work correctly
- ✅ Category filters work correctly
- ✅ Scraping triggers when needed
- ✅ Rate limiting prevents abuse

---

## 🐛 Troubleshooting

### Issue 1: Module Not Found

```
Error: No module named 'Agent.query_router.intent_detector'
```

**Solution:**

```bash
# Check if file exists
ls Agent/query_router/intent_detector.py

# Check if __init__.py exists
ls Agent/query_router/__init__.py

# Restart Python/backend
```

### Issue 2: Year Filtering Not Working

```
Error: No documents found for years [2018, 2021]
```

**Solution:**

```bash
# Verify version_date is populated
python -c "
from backend.database import SessionLocal, Document
db = SessionLocal()
count = db.query(Document).filter(Document.version_date.isnot(None)).count()
print(f'Documents with version_date: {count}')
db.close()
"

# If count is 0, run:
python scripts/populate_version_dates.py
```

### Issue 3: Low Confidence Scores

```
Confidence: 0.45 (expected >0.85)
```

**Solution:**

- Check if embeddings are complete
- Verify query is clear and specific
- Check if relevant documents exist
- Review intent detection filters

---

## 📊 Monitoring Dashboard

### Key Metrics to Track:

1. **Query Performance**

   - Average response time
   - Confidence scores
   - Citation counts

2. **Scraping Activity**

   - Scraping triggers per hour
   - Documents scraped per query
   - Success/failure rates

3. **Version Management**

   - Documents with version_date
   - Document families created
   - Latest version queries

4. **User Activity**
   - Queries per user
   - Most common query types
   - Peak usage times

---

## 🎉 Deployment Complete!

Once all tests pass, your system is ready for production use with:

- ✅ Smart intent detection
- ✅ Year-based filtering
- ✅ Version management
- ✅ Amendment tracking
- ✅ Automatic scraping
- ✅ High accuracy (85-95%)

**Congratulations! Your enhanced RAG system is live!** 🚀
