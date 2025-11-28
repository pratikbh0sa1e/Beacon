# Data Ingestion Module

## Overview
This module enables syncing documents from external ministry databases (PostgreSQL) into the RAG system. Documents are fetched, processed using existing OCR/text extraction, and stored without immediate embedding (lazy RAG).

## Architecture

```
External Ministry DB → DB Connector → Document Processor → Your RAG System
                                              ↓
                                    (Reuses existing pipeline)
                                    - Text Extraction (PDF/DOCX/Images)
                                    - OCR (EasyOCR)
                                    - Supabase Storage
                                    - PostgreSQL Metadata
                                    - Lazy Embedding
```

## Components

### 1. **models.py**
- `ExternalDataSource`: Registry of external databases
- `SyncLog`: History of sync operations

### 2. **db_connector.py**
- Connect to external PostgreSQL databases
- Fetch documents (as BLOBs or file paths)
- Test connections
- Encrypt/decrypt passwords

### 3. **document_processor.py**
- Process fetched documents
- Reuses existing `text_extractor.py` (PDF, DOCX, OCR)
- Uploads to Supabase
- Saves to your database

### 4. **sync_service.py**
- Orchestrates sync operations
- Handles full and incremental syncs
- Creates sync logs

### 5. **scheduler.py**
- Background scheduler for daily syncs
- Runs at 2 AM by default
- Can trigger manual syncs

## Setup

### 1. Generate Encryption Key
```bash
python Agent/data_ingestion/generate_key.py
```

Add the generated key to `.env`:
```env
DB_ENCRYPTION_KEY=your_generated_key_here
```

### 2. Run Database Migration
```bash
alembic revision --autogenerate -m "Add external data sources"
alembic upgrade head
```

### 3. Install Dependencies
```bash
pip install schedule psycopg2-binary cryptography
```

### 4. Start Server
The scheduler starts automatically when you run:
```bash
uvicorn backend.main:app --reload
```

## API Endpoints

### Register External Data Source
```bash
POST /data-sources/create
{
  "name": "MoE_Primary_DB",
  "ministry_name": "Ministry of Education",
  "description": "Primary database for MoE documents",
  "host": "ministry-db.example.com",
  "port": 5432,
  "database_name": "moe_docs",
  "username": "readonly_user",
  "password": "secure_password",
  "table_name": "documents",
  "file_column": "file_data",
  "filename_column": "filename",
  "metadata_columns": ["department", "date_created", "doc_type"],
  "sync_enabled": true,
  "sync_frequency": "daily"
}
```

### List Data Sources
```bash
GET /data-sources/list
GET /data-sources/list?ministry_name=Education
```

### Get Data Source Details
```bash
GET /data-sources/{source_id}
```

### Update Data Source
```bash
PUT /data-sources/{source_id}
{
  "sync_enabled": false,
  "description": "Updated description"
}
```

### Delete Data Source
```bash
DELETE /data-sources/{source_id}
```

### Test Connection
```bash
POST /data-sources/test-connection
{
  "host": "ministry-db.example.com",
  "port": 5432,
  "database_name": "moe_docs",
  "username": "readonly_user",
  "password": "secure_password"
}
```

### Trigger Manual Sync
```bash
# Sync specific source
POST /data-sources/{source_id}/sync
POST /data-sources/{source_id}/sync?limit=10&force_full=true

# Sync all enabled sources
POST /data-sources/sync-all
```

### View Sync Logs
```bash
# Logs for specific source
GET /data-sources/{source_id}/sync-logs?limit=10

# All recent logs
GET /data-sources/sync-logs/all?limit=50
```

## Database Schema

### External Data Source Table
```sql
CREATE TABLE external_data_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL,
    ministry_name VARCHAR(200) NOT NULL,
    description TEXT,
    
    -- Connection
    db_type VARCHAR(50) DEFAULT 'postgresql',
    host VARCHAR(255) NOT NULL,
    port INTEGER DEFAULT 5432,
    database_name VARCHAR(100) NOT NULL,
    username VARCHAR(100) NOT NULL,
    password_encrypted TEXT NOT NULL,
    
    -- Document config
    table_name VARCHAR(100),
    file_column VARCHAR(100),
    filename_column VARCHAR(100),
    metadata_columns JSON,
    
    -- Sync config
    sync_enabled BOOLEAN DEFAULT TRUE,
    sync_frequency VARCHAR(20) DEFAULT 'daily',
    last_sync_at TIMESTAMP,
    last_sync_status VARCHAR(20),
    last_sync_message TEXT,
    total_documents_synced INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Sync Log Table
```sql
CREATE TABLE sync_logs (
    id SERIAL PRIMARY KEY,
    source_id INTEGER NOT NULL,
    source_name VARCHAR(200) NOT NULL,
    status VARCHAR(20) NOT NULL,
    documents_fetched INTEGER DEFAULT 0,
    documents_processed INTEGER DEFAULT 0,
    documents_failed INTEGER DEFAULT 0,
    error_message TEXT,
    sync_duration_seconds INTEGER,
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);
```

## Usage Example

### 1. Register Ministry Database
```python
import requests

response = requests.post("http://localhost:8000/data-sources/create", json={
    "name": "AICTE_Documents",
    "ministry_name": "AICTE",
    "host": "aicte-db.gov.in",
    "port": 5432,
    "database_name": "documents",
    "username": "readonly",
    "password": "secure123",
    "table_name": "policy_docs",
    "file_column": "pdf_data",
    "filename_column": "doc_name",
    "metadata_columns": ["category", "year", "status"]
})

source_id = response.json()["source_id"]
```

### 2. Test Connection
```python
response = requests.post("http://localhost:8000/data-sources/test-connection", json={
    "host": "aicte-db.gov.in",
    "port": 5432,
    "database_name": "documents",
    "username": "readonly",
    "password": "secure123"
})

print(response.json())  # {"status": "success", "message": "Connection successful"}
```

### 3. Trigger Sync
```python
# Manual sync
response = requests.post(f"http://localhost:8000/data-sources/{source_id}/sync")
print(response.json())  # {"status": "sync_started", ...}

# Check logs after a few minutes
logs = requests.get(f"http://localhost:8000/data-sources/{source_id}/sync-logs")
print(logs.json())
```

### 4. Query Synced Documents
Once synced, documents are available through existing endpoints:
```python
# List all documents
docs = requests.get("http://localhost:8000/documents/list")

# Search with RAG agent
response = requests.post("http://localhost:8000/chat/query", json={
    "question": "What are AICTE's latest policies?",
    "thread_id": "session_1"
})
```

## Scheduler Configuration

The scheduler runs daily at 2 AM by default. To change:

```python
# In backend/main.py
start_scheduler(sync_time="03:30")  # 3:30 AM
```

## Security Best Practices

1. **Encryption Key**: Store `DB_ENCRYPTION_KEY` securely, never commit to git
2. **Read-Only Access**: Use read-only database users for external connections
3. **Network Security**: Use VPN or SSH tunnels for database connections
4. **SSL/TLS**: Enable SSL for PostgreSQL connections
5. **Credentials Rotation**: Regularly update database passwords

## Troubleshooting

### Connection Fails
```bash
# Test connection first
curl -X POST http://localhost:8000/data-sources/test-connection \
  -H "Content-Type: application/json" \
  -d '{"host": "...", "port": 5432, ...}'
```

### Sync Fails
```bash
# Check logs
curl http://localhost:8000/data-sources/{source_id}/sync-logs

# Check server logs
tail -f Agent/agent_logs/pipeline.log
```

### Documents Not Appearing
- Check sync logs for errors
- Verify table/column names in data source config
- Ensure file_column contains valid data (bytes or paths)

## Extending

### Support MySQL
Update `db_connector.py` to use `mysql-connector-python`:
```python
import mysql.connector

conn = mysql.connector.connect(
    host=host,
    port=port,
    database=database,
    user=username,
    password=password
)
```

### Add S3 Support
Create `s3_connector.py` to fetch from S3 buckets:
```python
import boto3

s3 = boto3.client('s3')
response = s3.get_object(Bucket='ministry-docs', Key='file.pdf')
file_data = response['Body'].read()
```

### Custom Processing
Extend `document_processor.py` for ministry-specific processing:
```python
def process_ministry_specific(self, file_data, ministry_name):
    if ministry_name == "MoE":
        # Custom MoE processing
        pass
```

## Integration with Existing System

This module seamlessly integrates with your existing:
- ✅ Text extraction (PDF, DOCX, OCR)
- ✅ Supabase storage
- ✅ Lazy RAG (no immediate embedding)
- ✅ Citation tracking
- ✅ Metadata extraction
- ✅ Hybrid search
- ✅ RAG agent

Documents from external sources flow through the same pipeline as uploaded documents.

## Future Enhancements

- [ ] Support for MongoDB, MySQL, Oracle
- [ ] S3/Azure Blob storage connectors
- [ ] SharePoint integration
- [ ] Real-time sync (webhooks)
- [ ] Conflict resolution for duplicate documents
- [ ] Data source health monitoring
- [ ] Sync analytics dashboard
