# Government Policy Intelligence Platform - Backend

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Make sure your `.env` file contains:
```
DATABASE_URL=postgresql://user:password@host:port/database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_BUCKET_NAME=policy-documents
```

### 3. Initialize Database
```bash
# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migration
alembic upgrade head
```

### 4. Run the Server
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Upload Documents
```
POST /documents/upload
Content-Type: multipart/form-data

files: [file1.pdf, file2.docx, file3.png]
```

### List Documents
```
GET /documents/list
```

### Get Document by ID
```
GET /documents/{document_id}
```

## Supported File Types
- PDF (.pdf)
- Word Documents (.docx)
- Images (.jpeg, .jpg, .png)

## Features
- Multi-file upload
- Text extraction (OCR for images)
- Supabase S3 storage
- PostgreSQL database with SQLAlchemy
- Automatic metadata tracking
