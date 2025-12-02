# Setup Checklist - Role-Based RAG

## Pre-Setup Requirements

- [ ] PostgreSQL database running
- [ ] Python 3.11+ installed
- [ ] `.env` file configured with database credentials
- [ ] Supabase S3 configured (for file storage)

## Setup Steps

### 1. Install Dependencies
```bash
pip install pgvector==0.3.6
```
- [ ] pgvector installed successfully

### 2. Enable PGVector Extension
```bash
python scripts/enable_pgvector.py
```
- [ ] pgvector extension enabled in PostgreSQL
- [ ] `document_embeddings` table created
- [ ] No errors in output

### 3. Restart Server
```bash
# Stop current server (Ctrl+C)
python main.py
```
- [ ] Server restarted successfully
- [ ] No import errors
- [ ] API endpoints accessible

## Verification Steps

### 4. Test Database Connection
```bash
python -c "from backend.database import engine; print('✅ Database connected')"
```
- [ ] Database connection successful

### 5. Test PGVector
```bash
python -c "from Agent.vector_store.pgvector_store import PGVectorStore; store = PGVectorStore(); print('✅ PGVector working')"
```
- [ ] PGVector store initialized

### 6. Test Role-Based Access
```bash
# Upload a test document
curl -X POST http://localhost:8000/api/documents/upload \
  -H "Authorization: Bearer <your_token>" \
  -F "file=@test.pdf"
```
- [ ] Document uploaded successfully
- [ ] Document stored in Supabase S3

### 7. Test RAG Query
```bash
curl -X POST http://localhost:8000/api/chat/query \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{"question": "Test query"}'
```
- [ ] Query executed successfully
- [ ] Response includes citations
- [ ] Citations include `approval_status`

## Optional: Batch Embed Existing Documents

### 8. Embed All Documents
```bash
python scripts/batch_embed_documents.py
```
- [ ] All documents embedded successfully
- [ ] No errors in output

## Troubleshooting

### If pgvector extension fails:
```bash
# Ubuntu/Debian
sudo apt install postgresql-15-pgvector

# macOS
brew install pgvector

# Then retry step 2
```

### If database connection fails:
- [ ] Check `.env` file has correct credentials
- [ ] Verify PostgreSQL is running
- [ ] Test connection: `psql -h <host> -U <user> -d <database>`

### If no results in RAG:
- [ ] Run batch embedding (step 8)
- [ ] Check document approval_status is 'approved' or 'pending'
- [ ] Verify user has correct role and institution_id

## Success Criteria

✅ All checkboxes above are checked
✅ Server running without errors
✅ RAG queries return results with approval status
✅ Role-based filtering working (test with different user roles)

## Next Steps After Setup

1. **Frontend Updates**
   - [ ] Add approval status badges to citations
   - [ ] Show visibility level indicators
   - [ ] Display institution information

2. **Production Optimization**
   - [ ] Add HNSW index for better performance
   - [ ] Monitor query performance
   - [ ] Set up logging for role-based access

3. **Testing**
   - [ ] Test with different user roles
   - [ ] Test with different visibility levels
   - [ ] Test cross-institution access

## Support

- **Quick Start**: See `QUICK_START_ROLE_BASED_RAG.md`
- **Full Documentation**: See `ROLE_BASED_RAG_IMPLEMENTATION.md`
- **Implementation Details**: See `IMPLEMENTATION_COMPLETE.md`

---

**Status**: [ ] Setup Complete | [ ] In Progress | [ ] Not Started

**Date**: _______________

**Notes**: 
_______________________________________________________________________
_______________________________________________________________________
_______________________________________________________________________
