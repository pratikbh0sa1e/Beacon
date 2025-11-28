# Supabase Storage Support - Guide

## Overview

The data ingestion module now supports **two storage types** for external documents:

1. **Database Storage** (default): Documents stored as BLOBs in PostgreSQL
2. **Supabase Storage** (new): Documents stored in Supabase buckets, with file paths in PostgreSQL

## Use Cases

### Scenario 1: Database Storage (BLOB)
Your PostgreSQL table has documents stored directly:
```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255),
    file_data BYTEA,  -- Document stored here
    created_at TIMESTAMP
);
```

### Scenario 2: Supabase Storage (File Paths)
Your PostgreSQL table has file paths, actual files in Supabase:
```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255),
    file_path VARCHAR(500),  -- Path like "resume/john_doe.pdf"
    created_at TIMESTAMP
);
```

And files are stored in Supabase bucket:
```
Supabase Bucket: "ministry-docs"
├── resume/
│   ├── john_doe.pdf
│   ├── jane_smith.pdf
│   └── ...
```

## Configuration

### For Database Storage (Default)

```bash
curl -X POST http://localhost:8000/data-sources/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "MoE_DB",
    "ministry_name": "Ministry of Education",
    "host": "db.example.com",
    "port": 5432,
    "database_name": "docs",
    "username": "readonly",
    "password": "pass123",
    "table_name": "documents",
    "file_column": "file_data",
    "filename_column": "filename",
    "storage_type": "database"
  }'
```

### For Supabase Storage (New)

```bash
curl -X POST http://localhost:8000/data-sources/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "MoE_Supabase",
    "ministry_name": "Ministry of Education",
    "host": "db.example.com",
    "port": 5432,
    "database_name": "docs",
    "username": "readonly",
    "password": "pass123",
    "table_name": "documents",
    "file_column": "file_path",
    "filename_column": "filename",
    "storage_type": "supabase",
    "supabase_url": "https://your-project.supabase.co",
    "supabase_key": "your-supabase-anon-key",
    "supabase_bucket": "ministry-docs",
    "file_path_prefix": "resume/"
  }'
```

## Field Explanations

### Common Fields
- `name`: Unique identifier for this data source
- `ministry_name`: Name of ministry/department
- `host`, `port`, `database_name`: PostgreSQL connection details
- `username`, `password`: Database credentials (encrypted)
- `table_name`: Table containing document records
- `file_column`: Column with file data (BLOB) or file path (string)
- `filename_column`: Column with original filename

### Supabase-Specific Fields
- `storage_type`: Set to `"supabase"` to enable Supabase storage
- `supabase_url`: Your Supabase project URL
- `supabase_key`: Supabase API key (will be encrypted)
- `supabase_bucket`: Name of the storage bucket
- `file_path_prefix`: Optional prefix for file paths (e.g., "resume/")

## How It Works

### Database Storage Flow
```
PostgreSQL → Fetch BLOB → Extract Text → Process → Store
```

### Supabase Storage Flow
```
PostgreSQL → Get File Path → Fetch from Supabase → Extract Text → Process → Store
```

## Example: Resume Database

### Your Setup
- PostgreSQL database with resume metadata
- Actual PDF files in Supabase bucket "resumes"
- File paths like "resume/candidate_123.pdf"

### Configuration
```json
{
  "name": "Resume_DB",
  "ministry_name": "HR Department",
  "host": "hr-db.example.com",
  "port": 5432,
  "database_name": "hr_system",
  "username": "readonly",
  "password": "secure123",
  "table_name": "candidate_resumes",
  "file_column": "resume_path",
  "filename_column": "candidate_name",
  "metadata_columns": ["position", "experience_years", "skills"],
  "storage_type": "supabase",
  "supabase_url": "https://your-project.supabase.co",
  "supabase_key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "supabase_bucket": "resumes",
  "file_path_prefix": "resume/"
}
```

### What Happens During Sync

1. **Query PostgreSQL**:
   ```sql
   SELECT resume_path, candidate_name, position, experience_years, skills
   FROM candidate_resumes
   ```

2. **For each record**:
   - Get `resume_path` (e.g., "candidate_123.pdf")
   - Add prefix: "resume/candidate_123.pdf"
   - Fetch from Supabase bucket "resumes"
   - Extract text using OCR/PDF parser
   - Store in your RAG system

3. **Result**:
   - All resumes indexed and searchable
   - Source tracked: "Resume_DB"
   - Metadata preserved: position, experience, skills

## Python Example

```python
import requests

BASE_URL = "http://localhost:8000"

# Register Supabase-backed data source
response = requests.post(f"{BASE_URL}/data-sources/create", json={
    "name": "Resume_Supabase",
    "ministry_name": "HR Department",
    "host": "hr-db.example.com",
    "port": 5432,
    "database_name": "hr_system",
    "username": "readonly",
    "password": "secure123",
    "table_name": "candidate_resumes",
    "file_column": "resume_path",
    "filename_column": "candidate_name",
    "storage_type": "supabase",
    "supabase_url": "https://your-project.supabase.co",
    "supabase_key": "your-supabase-key",
    "supabase_bucket": "resumes",
    "file_path_prefix": "resume/"
})

source_id = response.json()["source_id"]
print(f"✅ Registered: {source_id}")

# Trigger sync
requests.post(f"{BASE_URL}/data-sources/{source_id}/sync?limit=10")
print("⏳ Syncing 10 resumes...")

# Wait and check
import time
time.sleep(30)

logs = requests.get(f"{BASE_URL}/data-sources/{source_id}/sync-logs")
print(f"✅ Synced {logs.json()['logs'][0]['documents_processed']} resumes")

# Query
response = requests.post(f"{BASE_URL}/chat/query", json={
    "question": "Find candidates with Python experience",
    "thread_id": "session_1"
})

print(response.json()["answer"])
```

## Security

### Encrypted Credentials
Both database passwords and Supabase keys are encrypted using Fernet:
- Stored encrypted in database
- Decrypted only when needed
- Same encryption key as database passwords

### Access Control
- Use **read-only** Supabase keys (anon key)
- Configure bucket policies for read-only access
- Never use service role keys

### Supabase Bucket Policy Example
```sql
-- Read-only policy for external access
CREATE POLICY "Allow read access"
ON storage.objects FOR SELECT
USING (bucket_id = 'resumes');
```

## Troubleshooting

### Supabase Connection Fails

**Error**: "Failed to fetch file from Supabase"

**Solutions**:
1. Verify Supabase URL and key:
   ```bash
   curl https://your-project.supabase.co/rest/v1/ \
     -H "apikey: your-key"
   ```

2. Check bucket name and file path:
   ```python
   from supabase import create_client
   client = create_client(url, key)
   files = client.storage.from_('resumes').list('resume/')
   print(files)
   ```

3. Verify bucket permissions

### File Not Found

**Error**: "Empty response for file"

**Solutions**:
1. Check file path in database matches Supabase
2. Verify `file_path_prefix` is correct
3. List files in bucket to confirm:
   ```python
   files = client.storage.from_('bucket').list('prefix/')
   ```

### Wrong Storage Type

**Error**: "Supabase fetcher not initialized"

**Solution**: Set `storage_type: "supabase"` when creating data source

## Migration Guide

### From Database Storage to Supabase

If you want to migrate from storing BLOBs to Supabase:

1. **Upload files to Supabase**:
   ```python
   from supabase import create_client
   import psycopg2
   
   # Connect to DB
   conn = psycopg2.connect(...)
   cursor = conn.cursor()
   
   # Get all documents
   cursor.execute("SELECT id, filename, file_data FROM documents")
   
   # Upload to Supabase
   client = create_client(url, key)
   for id, filename, file_data in cursor:
       path = f"documents/{filename}"
       client.storage.from_('bucket').upload(path, file_data)
       
       # Update DB with path
       cursor.execute(
           "UPDATE documents SET file_path = %s WHERE id = %s",
           (path, id)
       )
   
   conn.commit()
   ```

2. **Update data source configuration**:
   ```bash
   curl -X PUT http://localhost:8000/data-sources/1 \
     -H "Content-Type: application/json" \
     -d '{
       "storage_type": "supabase",
       "supabase_url": "...",
       "supabase_key": "...",
       "supabase_bucket": "bucket",
       "file_column": "file_path"
     }'
   ```

3. **Trigger re-sync**:
   ```bash
   curl -X POST http://localhost:8000/data-sources/1/sync?force_full=true
   ```

## Comparison

| Feature | Database Storage | Supabase Storage |
|---------|-----------------|------------------|
| **Storage** | PostgreSQL BLOB | Supabase Bucket |
| **DB Size** | Large (includes files) | Small (only paths) |
| **Scalability** | Limited by DB | Highly scalable |
| **Access Speed** | Fast (direct) | Network dependent |
| **Cost** | DB storage costs | S3-like pricing |
| **Best For** | Small datasets | Large datasets |

## Best Practices

1. **Use Supabase for**:
   - Large document collections (1000+)
   - Files > 1MB
   - Shared access across systems
   - Cost optimization

2. **Use Database for**:
   - Small document collections (<100)
   - Files < 100KB
   - Simple setup
   - Single system access

3. **Security**:
   - Always use read-only keys
   - Enable bucket policies
   - Encrypt credentials
   - Monitor access logs

4. **Performance**:
   - Use `file_path_prefix` to organize files
   - Limit initial syncs
   - Monitor Supabase bandwidth
   - Cache frequently accessed files

## Summary

You can now connect to databases where:
- ✅ Documents stored as BLOBs (original)
- ✅ Documents stored in Supabase with paths in DB (new)

Both work seamlessly with your existing RAG pipeline!

---

**Questions?** Check:
- Main guide: `DATA_INGESTION_GUIDE.md`
- Quick reference: `QUICK_REFERENCE_DATA_INGESTION.md`
