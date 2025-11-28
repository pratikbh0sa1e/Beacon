# External Data Ingestion - Complete Guide

## 🎯 Overview

This guide explains how to connect your RAG system to external ministry databases (PostgreSQL) to automatically sync and process documents.

**Problem Solved**: Ministry data scattered across multiple databases → Centralized RAG system with automated syncing

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    External Ministry DBs                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   MoE    │  │  AICTE   │  │   UGC    │  │  Others  │   │
│  │ Postgres │  │ Postgres │  │ Postgres │  │ Postgres │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
└───────┼─────────────┼─────────────┼─────────────┼──────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                          │
                    ┌─────▼─────┐
                    │    DB     │
                    │ Connector │
                    └─────┬─────┘
                          │
                    ┌─────▼─────┐
                    │ Document  │
                    │ Processor │
                    └─────┬─────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
   ┌────▼────┐      ┌────▼────┐      ┌────▼────┐
   │  Text   │      │ Supabase│      │Database │
   │Extractor│      │ Storage │      │Metadata │
   │(OCR/PDF)│      │         │      │         │
   └─────────┘      └─────────┘      └─────────┘
                          │
                    ┌─────▼─────┐
                    │ Lazy RAG  │
                    │ (Embed on │
                    │  demand)  │
                    └───────────┘
```

## 📦 Installation

### 1. Install Dependencies
```bash
pip install schedule psycopg2-binary cryptography
```

Or update from requirements.txt:
```bash
pip install -r requirements.txt
```

### 2. Generate Encryption Key
```bash
python scripts/setup_data_ingestion.py
```

This will:
- Generate a secure encryption key
- Save it to your `.env` file as `DB_ENCRYPTION_KEY`
- Check dependencies

### 3. Run Database Migration
```bash
alembic revision --autogenerate -m "Add external data sources"
alembic upgrade head
```

This creates two new tables:
- `external_data_sources` - Registry of ministry databases
- `sync_logs` - History of sync operations

### 4. Start Server
```bash
uvicorn backend.main:app --reload
```

The scheduler starts automatically and runs daily syncs at 2 AM.

## 🚀 Quick Start

### Step 1: Test Database Connection

Before registering a data source, test the connection:

```bash
curl -X POST http://localhost:8000/data-sources/test-connection \
  -H "Content-Type: application/json" \
  -d '{
    "host": "ministry-db.example.com",
    "port": 5432,
    "database_name": "documents",
    "username": "readonly_user",
    "password": "secure_password"
  }'
```

Response:
```json
{
  "status": "success",
  "message": "Connection successful"
}
```

### Step 2: Register Data Source

```bash
curl -X POST http://localhost:8000/data-sources/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "MoE_Primary_DB",
    "ministry_name": "Ministry of Education",
    "description": "Primary database for MoE documents",
    "host": "moe-db.example.com",
    "port": 5432,
    "database_name": "moe_documents",
    "username": "readonly_user",
    "password": "secure_password",
    "table_name": "policy_documents",
    "file_column": "document_data",
    "filename_column": "document_name",
    "metadata_columns": ["department", "policy_type", "date_published"],
    "sync_enabled": true,
    "sync_frequency": "daily"
  }'
```

Response:
```json
{
  "status": "success",
  "message": "Data source created successfully",
  "source_id": 1,
  "name": "MoE_Primary_DB"
}
```

### Step 3: Trigger Manual Sync

```bash
curl -X POST http://localhost:8000/data-sources/1/sync
```

Response:
```json
{
  "status": "sync_started",
  "source_id": 1,
  "source_name": "MoE_Primary_DB",
  "message": "Sync started in background"
}
```

### Step 4: Check Sync Status

```bash
curl http://localhost:8000/data-sources/1/sync-logs
```

Response:
```json
{
  "source_id": 1,
  "total_logs": 1,
  "logs": [
    {
      "id": 1,
      "status": "success",
      "documents_fetched": 25,
      "documents_processed": 25,
      "documents_failed": 0,
      "sync_duration_seconds": 45,
      "started_at": "2025-11-28T10:30:00",
      "completed_at": "2025-11-28T10:30:45"
    }
  ]
}
```

### Step 5: Query Synced Documents

Documents are now available through your RAG system:

```bash
curl -X POST http://localhost:8000/chat/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the latest MoE policies on higher education?",
    "thread_id": "session_1"
  }'
```

## 📚 API Reference

### Data Source Management

#### Create Data Source
```
POST /data-sources/create
```

**Body:**
```json
{
  "name": "string (unique)",
  "ministry_name": "string",
  "description": "string (optional)",
  "host": "string",
  "port": 5432,
  "database_name": "string",
  "username": "string",
  "password": "string (will be encrypted)",
  "table_name": "string",
  "file_column": "string",
  "filename_column": "string",
  "metadata_columns": ["string"] (optional),
  "sync_enabled": true,
  "sync_frequency": "daily"
}
```

#### List Data Sources
```
GET /data-sources/list
GET /data-sources/list?ministry_name=Education
```

#### Get Data Source
```
GET /data-sources/{source_id}
```

#### Update Data Source
```
PUT /data-sources/{source_id}
```

**Body:** (all fields optional)
```json
{
  "name": "string",
  "sync_enabled": false,
  "description": "string"
}
```

#### Delete Data Source
```
DELETE /data-sources/{source_id}
```

### Sync Operations

#### Test Connection
```
POST /data-sources/test-connection
```

#### Trigger Sync (Single Source)
```
POST /data-sources/{source_id}/sync
POST /data-sources/{source_id}/sync?limit=10&force_full=true
```

**Query Parameters:**
- `limit` (optional): Max documents to sync
- `force_full` (optional): Force full sync instead of incremental

#### Sync All Sources
```
POST /data-sources/sync-all
```

#### Get Sync Logs
```
GET /data-sources/{source_id}/sync-logs?limit=10
GET /data-sources/sync-logs/all?limit=50
```

## 🔧 Configuration

### Database Table Requirements

Your external database table should have:
1. **File column**: Contains document data (bytea/blob) or file path
2. **Filename column**: Original filename
3. **Metadata columns** (optional): Additional info to extract

Example table structure:
```sql
CREATE TABLE policy_documents (
    id SERIAL PRIMARY KEY,
    document_name VARCHAR(255),
    document_data BYTEA,  -- or file_path VARCHAR(500)
    department VARCHAR(100),
    policy_type VARCHAR(50),
    date_published DATE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Supported File Types

The system reuses your existing text extraction:
- ✅ PDF (.pdf)
- ✅ Word Documents (.docx)
- ✅ Images (.jpeg, .jpg, .png) with OCR

### Scheduler Configuration

Default: Daily sync at 2:00 AM

To change, edit `backend/main.py`:
```python
@app.on_event("startup")
async def startup_event():
    start_scheduler(sync_time="03:30")  # 3:30 AM
```

## 🔐 Security

### Password Encryption

All database passwords are encrypted using Fernet (symmetric encryption):
- Encryption key stored in `.env` as `DB_ENCRYPTION_KEY`
- Passwords encrypted before storage
- Decrypted only when needed for connections

### Best Practices

1. **Read-Only Access**: Use read-only database users
   ```sql
   CREATE USER readonly_user WITH PASSWORD 'secure_password';
   GRANT SELECT ON policy_documents TO readonly_user;
   ```

2. **Network Security**: Use VPN or SSH tunnels for database access

3. **SSL/TLS**: Enable SSL for PostgreSQL connections
   ```python
   # Future enhancement in db_connector.py
   conn = psycopg2.connect(..., sslmode='require')
   ```

4. **Credentials Rotation**: Regularly update passwords via API

5. **Backup Encryption Key**: Store `DB_ENCRYPTION_KEY` securely

## 📊 Monitoring

### Check Data Source Status
```bash
curl http://localhost:8000/data-sources/list
```

Look for:
- `last_sync_at`: When last sync occurred
- `last_sync_status`: success/failed/in_progress
- `total_documents_synced`: Total docs synced

### View Sync Logs
```bash
curl http://localhost:8000/data-sources/sync-logs/all?limit=20
```

### Check Server Logs
```bash
tail -f Agent/agent_logs/pipeline.log
```

## 🐛 Troubleshooting

### Connection Fails

**Problem**: Cannot connect to external database

**Solutions**:
1. Test connection first:
   ```bash
   curl -X POST http://localhost:8000/data-sources/test-connection ...
   ```

2. Check network access (firewall, VPN)

3. Verify credentials

4. Check PostgreSQL is accepting connections:
   ```bash
   psql -h HOST -U USER -d DATABASE
   ```

### Sync Fails

**Problem**: Sync logs show failures

**Solutions**:
1. Check sync logs for error message:
   ```bash
   curl http://localhost:8000/data-sources/{id}/sync-logs
   ```

2. Verify table/column names in data source config

3. Check file_column contains valid data

4. Review server logs:
   ```bash
   tail -f Agent/agent_logs/pipeline.log
   ```

### Documents Not Appearing

**Problem**: Sync succeeds but documents not queryable

**Solutions**:
1. Check if documents were actually processed:
   ```bash
   curl http://localhost:8000/documents/list
   ```

2. Verify file format is supported (PDF, DOCX, images)

3. Check if text extraction succeeded (check extracted_text field)

4. Trigger embedding if needed:
   ```bash
   curl -X POST http://localhost:8000/documents/embed \
     -d '{"doc_ids": [1, 2, 3]}'
   ```

### Scheduler Not Running

**Problem**: Daily syncs not happening

**Solutions**:
1. Check server logs for scheduler startup message

2. Verify server is running continuously (not restarting)

3. Manually trigger sync to test:
   ```bash
   curl -X POST http://localhost:8000/data-sources/sync-all
   ```

## 🎓 Example Scenarios

### Scenario 1: Ministry of Education

**Setup**: MoE has a PostgreSQL database with policy documents

```python
import requests

# Register MoE database
response = requests.post("http://localhost:8000/data-sources/create", json={
    "name": "MoE_Policies",
    "ministry_name": "Ministry of Education",
    "host": "moe-db.gov.in",
    "port": 5432,
    "database_name": "policies",
    "username": "readonly",
    "password": "secure123",
    "table_name": "education_policies",
    "file_column": "policy_pdf",
    "filename_column": "policy_name",
    "metadata_columns": ["category", "year", "status"]
})

source_id = response.json()["source_id"]

# Trigger initial sync
requests.post(f"http://localhost:8000/data-sources/{source_id}/sync")

# Query after sync
response = requests.post("http://localhost:8000/chat/query", json={
    "question": "What are the new education policies for 2025?",
    "thread_id": "session_1"
})

print(response.json()["answer"])
```

### Scenario 2: Multiple Ministries

**Setup**: Connect 5 different ministry databases

```python
ministries = [
    {"name": "MoE_DB", "ministry": "Ministry of Education", "host": "moe-db.gov.in"},
    {"name": "AICTE_DB", "ministry": "AICTE", "host": "aicte-db.gov.in"},
    {"name": "UGC_DB", "ministry": "UGC", "host": "ugc-db.gov.in"},
    {"name": "NCERT_DB", "ministry": "NCERT", "host": "ncert-db.gov.in"},
    {"name": "NIOS_DB", "ministry": "NIOS", "host": "nios-db.gov.in"}
]

for ministry in ministries:
    requests.post("http://localhost:8000/data-sources/create", json={
        "name": ministry["name"],
        "ministry_name": ministry["ministry"],
        "host": ministry["host"],
        # ... other config
    })

# Sync all at once
requests.post("http://localhost:8000/data-sources/sync-all")
```

### Scenario 3: Incremental Daily Sync

**Setup**: Only sync new documents added since last sync

```python
# Initial full sync
requests.post("http://localhost:8000/data-sources/1/sync?force_full=true")

# Daily syncs (automatic via scheduler)
# Or manual: requests.post("http://localhost:8000/data-sources/1/sync")

# Check what was synced
logs = requests.get("http://localhost:8000/data-sources/1/sync-logs")
for log in logs.json()["logs"]:
    print(f"{log['started_at']}: {log['documents_processed']} new docs")
```

## 🚀 Advanced Usage

### Custom Metadata Extraction

Extend `document_processor.py` to extract ministry-specific metadata:

```python
def process_document(self, file_data, filename, source_name, metadata):
    # ... existing code ...
    
    # Custom metadata for MoE
    if source_name.startswith("MoE"):
        metadata["ministry_specific"] = {
            "policy_number": extract_policy_number(filename),
            "effective_date": extract_date(extracted_text)
        }
    
    # ... rest of processing ...
```

### Multiple Database Types

Currently supports PostgreSQL. To add MySQL:

```python
# In db_connector.py
import mysql.connector

def fetch_documents_mysql(self, ...):
    conn = mysql.connector.connect(
        host=host,
        port=port,
        database=database,
        user=username,
        password=password
    )
    # ... fetch logic ...
```

### S3 Integration

To fetch documents from S3 instead of database:

```python
# Create Agent/data_ingestion/s3_connector.py
import boto3

class S3Connector:
    def fetch_documents(self, bucket, prefix):
        s3 = boto3.client('s3')
        objects = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
        
        for obj in objects['Contents']:
            file_data = s3.get_object(Bucket=bucket, Key=obj['Key'])['Body'].read()
            yield {
                "file_data": file_data,
                "filename": obj['Key'].split('/')[-1],
                "metadata": {"s3_key": obj['Key']}
            }
```

## 📈 Performance

### Sync Performance
- **Small documents** (<1MB): ~2-3 seconds per document
- **Large documents** (>5MB): ~5-10 seconds per document
- **Batch processing**: Parallel processing for multiple documents

### Optimization Tips
1. **Limit initial sync**: Use `?limit=100` for testing
2. **Schedule off-peak**: Run syncs at night (2 AM default)
3. **Incremental syncs**: Only fetch new documents
4. **Connection pooling**: Reuse database connections

## 🎯 Integration with Existing Features

This module seamlessly integrates with:

✅ **Text Extraction**: Reuses `backend/utils/text_extractor.py`
✅ **OCR**: EasyOCR for scanned documents
✅ **Supabase Storage**: Documents stored in S3
✅ **Lazy RAG**: No immediate embedding (on-demand)
✅ **Citation Tracking**: Source metadata preserved
✅ **Hybrid Search**: BM25 + Vector search
✅ **RAG Agent**: Documents queryable via chat

## 📝 Summary

You've successfully extended your RAG system to:
1. ✅ Connect to external ministry databases
2. ✅ Automatically sync documents daily
3. ✅ Process PDFs, DOCX, and images with OCR
4. ✅ Store without immediate embedding (lazy RAG)
5. ✅ Track source for citations
6. ✅ Query via existing RAG agent

**Next Steps**:
- Register your ministry databases
- Test with small batches first
- Monitor sync logs
- Scale to production

**Support**:
- API Docs: http://localhost:8000/docs
- Module README: Agent/data_ingestion/README.md
- Example Script: scripts/example_data_source_setup.py
