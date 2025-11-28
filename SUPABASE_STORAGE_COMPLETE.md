# ✅ Supabase Storage Support - Complete

## 🎉 Feature Added!

Your data ingestion module now supports **two storage types**:

### 1. Database Storage (Original)
Documents stored as BLOBs directly in PostgreSQL

### 2. Supabase Storage (New)
Documents stored in Supabase buckets, with file paths in PostgreSQL

## 🎯 Your Use Case Solved

**Your Scenario**: 
- PostgreSQL database with document metadata
- Actual PDF files stored in Supabase bucket under "resume/" folder
- Need to sync and index these documents

**Solution**:
```bash
curl -X POST http://localhost:8000/data-sources/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Resume_DB",
    "ministry_name": "HR Department",
    "host": "your-db-host",
    "port": 5432,
    "database_name": "hr_system",
    "username": "readonly",
    "password": "your-password",
    "table_name": "resumes",
    "file_column": "file_path",
    "filename_column": "candidate_name",
    "storage_type": "supabase",
    "supabase_url": "https://your-project.supabase.co",
    "supabase_key": "your-supabase-anon-key",
    "supabase_bucket": "your-bucket-name",
    "file_path_prefix": "resume/"
  }'
```

## 📦 What Was Added

### New Files (1)
- `Agent/data_ingestion/supabase_fetcher.py` - Fetch files from Supabase storage

### Updated Files (4)
- `backend/database.py` - Added Supabase configuration fields
- `backend/routers/data_source_router.py` - Added Supabase parameters to API
- `Agent/data_ingestion/document_processor.py` - Added Supabase document processing
- `Agent/data_ingestion/sync_service.py` - Added Supabase sync logic

### Documentation (1)
- `SUPABASE_STORAGE_GUIDE.md` - Complete guide for Supabase storage

### Database Migration
- New fields added to `external_data_sources` table:
  - `storage_type` - "database" or "supabase"
  - `supabase_url` - Supabase project URL
  - `supabase_key_encrypted` - Encrypted Supabase key
  - `supabase_bucket` - Bucket name
  - `file_path_prefix` - Optional path prefix

## 🚀 How to Use

### Step 1: Register Data Source
```python
import requests

response = requests.post("http://localhost:8000/data-sources/create", json={
    "name": "Resume_Supabase",
    "ministry_name": "HR",
    "host": "db.example.com",
    "port": 5432,
    "database_name": "hr",
    "username": "readonly",
    "password": "pass123",
    "table_name": "resumes",
    "file_column": "resume_path",  # Column with file path
    "filename_column": "candidate_name",
    "storage_type": "supabase",  # Enable Supabase
    "supabase_url": "https://your-project.supabase.co",
    "supabase_key": "your-key",
    "supabase_bucket": "resumes",
    "file_path_prefix": "resume/"  # Files are in resume/ folder
})

source_id = response.json()["source_id"]
```

### Step 2: Trigger Sync
```python
requests.post(f"http://localhost:8000/data-sources/{source_id}/sync")
```

### Step 3: Query Documents
```python
response = requests.post("http://localhost:8000/chat/query", json={
    "question": "Find candidates with Python experience",
    "thread_id": "session_1"
})

print(response.json()["answer"])
```

## 🔄 How It Works

### Sync Flow
```
1. Query PostgreSQL
   SELECT resume_path, candidate_name FROM resumes

2. For each record:
   - Get file_path: "candidate_123.pdf"
   - Add prefix: "resume/candidate_123.pdf"
   - Fetch from Supabase bucket
   - Extract text (PDF/OCR)
   - Store in RAG system

3. Documents now searchable!
```

## 🔐 Security

### Encrypted Credentials
- Supabase keys encrypted using same Fernet key
- Stored encrypted in database
- Decrypted only when needed

### Best Practices
- Use **read-only** Supabase keys (anon key)
- Never use service role keys
- Configure bucket policies for read-only access

## 📊 Comparison

| Feature | Database Storage | Supabase Storage |
|---------|-----------------|------------------|
| **Setup** | Simple | Requires Supabase config |
| **DB Size** | Large | Small (only paths) |
| **Scalability** | Limited | Highly scalable |
| **Best For** | Small datasets | Large datasets |

## ✅ Migration Applied

Database migration completed:
```
✅ Added storage_type column
✅ Added supabase_url column
✅ Added supabase_key_encrypted column
✅ Added supabase_bucket column
✅ Added file_path_prefix column
```

## 🎓 Example Scenarios

### Scenario 1: Resume Database
- **DB**: PostgreSQL with candidate info
- **Storage**: Supabase bucket "resumes"
- **Folder**: "resume/"
- **Files**: candidate_123.pdf, candidate_456.pdf

### Scenario 2: Policy Documents
- **DB**: PostgreSQL with policy metadata
- **Storage**: Supabase bucket "policies"
- **Folder**: "education/2025/"
- **Files**: policy_001.pdf, policy_002.pdf

### Scenario 3: Mixed Storage
- **Source 1**: Database storage (small docs)
- **Source 2**: Supabase storage (large docs)
- Both work together in same RAG system!

## 📚 Documentation

- **Complete Guide**: `SUPABASE_STORAGE_GUIDE.md`
- **Quick Reference**: `QUICK_REFERENCE_DATA_INGESTION.md`
- **Main Guide**: `DATA_INGESTION_GUIDE.md`

## 🐛 Troubleshooting

### Connection Fails
```python
# Test Supabase connection
from supabase import create_client
client = create_client(url, key)
files = client.storage.from_('bucket').list('folder/')
print(files)
```

### File Not Found
- Check file path in database
- Verify `file_path_prefix` is correct
- List files in bucket to confirm

### Wrong Storage Type
- Ensure `storage_type: "supabase"` is set
- Verify all Supabase fields are provided

## 🎉 Summary

You can now connect to databases where documents are stored in Supabase buckets!

**What works**:
- ✅ Fetch files from Supabase storage
- ✅ Extract text (PDF, DOCX, images with OCR)
- ✅ Store in RAG system
- ✅ Query via existing agent
- ✅ Track source for citations
- ✅ Encrypted credentials
- ✅ Daily automated syncs

**Your specific case**:
- ✅ PostgreSQL with file paths
- ✅ PDFs in Supabase bucket
- ✅ Files under "resume/" folder
- ✅ All handled automatically!

---

**Ready to use!** Just register your data source with `storage_type: "supabase"` and provide Supabase credentials.

**Questions?** Check `SUPABASE_STORAGE_GUIDE.md` for detailed examples.
