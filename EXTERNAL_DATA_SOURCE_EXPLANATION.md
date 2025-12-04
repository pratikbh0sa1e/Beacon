# External Data Source System - Complete Explanation

## 📋 Current Status

### ✅ **Already Implemented (Backend)**

The backend infrastructure is **fully functional** and includes:

1. **Database Models** (`backend/database.py`)

   - `ExternalDataSource` table with all connection details
   - `SyncLog` table for tracking sync operations
   - Password encryption support
   - Supabase/S3 storage configuration

2. **API Endpoints** (`backend/routers/data_source_router.py`)

   - ✅ Create data source
   - ✅ List data sources
   - ✅ Get data source details
   - ✅ Update data source
   - ✅ Delete data source
   - ✅ Test connection
   - ✅ Trigger manual sync
   - ✅ Sync all sources
   - ✅ Get sync logs

3. **Core Services** (`Agent/data_ingestion/`)
   - Database connector with encryption
   - Sync service for automated data ingestion
   - Background task support

### ❌ **Not Yet Implemented (Frontend + Enhanced Features)**

The following are **planned but not built**:

1. **Frontend UI** - No pages exist yet
2. **Request/Approval Workflow** - Currently direct creation only
3. **Visibility Controls** - Not enforced yet
4. **Notifications** - Not integrated

---

## 🏗️ How It Currently Works

### **Architecture Overview**

```
External Ministry DB → BEACON Backend → Document Storage → RAG System
                           ↓
                    Sync Service
                           ↓
                    Document Metadata
                           ↓
                    Vector Embeddings
```

### **Current Flow (Developer Only)**

1. **Developer** creates data source via API:

   ```bash
   POST /data-sources/create
   {
     "name": "Ministry of Health Database",
     "ministry_name": "Ministry of Health",
     "host": "health.gov.in",
     "port": 5432,
     "database_name": "health_docs",
     "username": "readonly_user",
     "password": "encrypted_password",
     "table_name": "documents",
     "file_column": "file_data",
     "filename_column": "filename"
   }
   ```

2. **System** encrypts password and stores configuration

3. **Sync Service** connects to external database:

   - Queries the specified table
   - Fetches documents (files or file paths)
   - Downloads files if stored in Supabase/S3
   - Extracts text from documents
   - Creates Document records in BEACON
   - Generates metadata
   - Logs sync operation

4. **Documents** become searchable in BEACON:
   - Available in document explorer
   - Indexed for RAG queries
   - Embedded for semantic search

### **Data Flow Diagram**

```
┌─────────────────────────────────────────────────────────────┐
│                    External Ministry DB                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Table: documents                                      │  │
│  │ - id                                                  │  │
│  │ - filename                                            │  │
│  │ - file_data (bytea) OR file_path (text)             │  │
│  │ - metadata (json)                                     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    Sync Service Queries
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    BEACON Backend                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ ExternalDataSource (config)                          │  │
│  │ - Connection details                                  │  │
│  │ - Sync schedule                                       │  │
│  │ - Last sync status                                    │  │
│  └──────────────────────────────────────────────────────┘  │
│                            ↓                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Sync Service                                          │  │
│  │ 1. Connect to external DB                            │  │
│  │ 2. Fetch documents                                    │  │
│  │ 3. Download files (if S3/Supabase)                   │  │
│  │ 4. Extract text                                       │  │
│  │ 5. Create Document records                           │  │
│  │ 6. Generate metadata                                  │  │
│  │ 7. Log sync operation                                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                            ↓                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Document Storage                                      │  │
│  │ - Documents table                                     │  │
│  │ - DocumentMetadata table                             │  │
│  │ - Files in Supabase S3                               │  │
│  └──────────────────────────────────────────────────────┘  │
│                            ↓                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ RAG System                                            │  │
│  │ - Vector embeddings (pgvector)                       │  │
│  │ - Semantic search                                     │  │
│  │ - AI-powered queries                                  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    Users Query Documents
```

---

## 🎯 Planned Implementation (Not Built Yet)

### **Phase 1: Request & Approval Workflow**

#### **What We'll Build:**

1. **Request Form** (Frontend)

   - Ministry/University admins can request connections
   - Form fields: DB credentials, table config, classification
   - Test connection before submit
   - Submit request for developer approval

2. **My Requests Page** (Frontend)

   - View submitted requests
   - Track status (Pending/Approved/Rejected)
   - See rejection reasons
   - Resubmit rejected requests

3. **Approval Dashboard** (Frontend - Developer Only)

   - View all pending requests
   - Test connections
   - Approve/reject with notes
   - View approval history

4. **Backend Enhancements**
   - Add request workflow fields to database
   - New endpoints for request submission
   - Approval/rejection logic
   - Notification integration

#### **Database Changes Needed:**

```sql
ALTER TABLE external_data_sources ADD COLUMN:
- institution_id (link to ministry/university)
- requested_by_user_id (who requested)
- approved_by_user_id (who approved)
- request_status (pending/approved/rejected)
- data_classification (public/educational/confidential/institutional)
- request_notes (requester's notes)
- rejection_reason (if rejected)
- requested_at (timestamp)
- approved_at (timestamp)
```

### **Phase 2: Visibility Controls**

#### **Data Classification System:**

| Classification    | Set By           | Visible To                           |
| ----------------- | ---------------- | ------------------------------------ |
| **Public**        | Ministry Admin   | Everyone (all users, public viewers) |
| **Educational**   | Ministry Admin   | All universities + All ministries    |
| **Confidential**  | Ministry Admin   | Only that ministry + Developer       |
| **Institutional** | University Admin | Only that university                 |

#### **How It Works:**

1. **When Requesting:**

   - Ministry Admin selects classification from dropdown
   - University Admin gets "Institutional" automatically

2. **When Syncing:**

   - Documents inherit classification from data source
   - `visibility_level` set based on classification
   - `institution_id` set for restricted docs

3. **When Querying:**
   - RAG system filters by user role and institution
   - Users only see documents they have access to

#### **Access Control Matrix:**

| User Role        | Can See                                                  |
| ---------------- | -------------------------------------------------------- |
| Developer        | ALL documents                                            |
| Ministry Admin   | Public + Educational + Their ministry's Confidential     |
| University Admin | Public + Educational + Their institution's Institutional |
| Student          | Public + Educational + Their institution's Institutional |
| Public Viewer    | Public only                                              |

### **Phase 3: Enhanced Features**

1. **Scheduled Syncs**

   - Cron jobs for automatic syncing
   - Configurable frequency (hourly/daily/weekly)
   - Retry failed syncs

2. **Sync Monitoring**

   - Real-time sync status
   - Progress indicators
   - Error notifications
   - Sync history dashboard

3. **Advanced Configuration**
   - Custom SQL queries
   - Field mapping
   - Data transformation rules
   - Incremental sync (only new docs)

---

## 🔧 Technical Implementation Details

### **Current Backend Components:**

#### **1. ExternalDBConnector** (`Agent/data_ingestion/db_connector.py`)

```python
class ExternalDBConnector:
    def connect(host, port, database, username, password):
        # Establishes PostgreSQL connection

    def test_connection():
        # Validates credentials and connectivity

    def fetch_documents(table, columns):
        # Queries external database

    def encrypt_password(password):
        # Encrypts passwords before storage

    def decrypt_password(encrypted):
        # Decrypts for connection
```

#### **2. SyncService** (`Agent/data_ingestion/sync_service.py`)

```python
class SyncService:
    def sync_source(source_id, db, limit=None):
        # Syncs single data source
        # 1. Connect to external DB
        # 2. Fetch documents
        # 3. Process each document
        # 4. Create Document records
        # 5. Log sync operation

    def sync_all_sources(db):
        # Syncs all enabled sources

    def process_document(file_data, filename, metadata):
        # Extracts text
        # Uploads to Supabase
        # Creates database record
```

#### **3. API Endpoints** (Already Built)

**Create Data Source:**

```
POST /data-sources/create
Access: Developer only
Body: Connection details + sync config
Returns: Source ID
```

**List Data Sources:**

```
GET /data-sources/list
Access: Developer only
Returns: All configured sources with sync status
```

**Trigger Sync:**

```
POST /data-sources/{id}/sync
Access: Developer only
Action: Starts background sync task
Returns: Sync started confirmation
```

**Get Sync Logs:**

```
GET /data-sources/{id}/sync-logs
Access: Developer only
Returns: Sync history with stats
```

### **What Needs to Be Built:**

#### **1. Frontend Pages** (None exist yet)

**DataSourceRequestPage.jsx:**

```jsx
// Form for Ministry/University admins to request connections
// Fields: DB credentials, table config, classification
// Features: Test connection, submit request
```

**MyDataSourceRequestsPage.jsx:**

```jsx
// View user's submitted requests
// Show status, rejection reasons
// Allow resubmission
```

**DataSourceApprovalPage.jsx:**

```jsx
// Developer dashboard for approving requests
// Tabs: Pending, Approved, Rejected
// Actions: Test, Approve, Reject
```

**DataSourcesPage.jsx:**

```jsx
// View active data sources (Developer only)
// Trigger manual syncs
// View sync logs
// Edit/delete sources
```

#### **2. Backend Enhancements**

**New Endpoints Needed:**

```python
POST /data-sources/request
# Submit connection request (Ministry/University Admin)

GET /data-sources/my-requests
# Get user's requests

GET /data-sources/requests/pending
# Get pending requests (Developer)

POST /data-sources/requests/{id}/approve
# Approve request (Developer)

POST /data-sources/requests/{id}/reject
# Reject request (Developer)
```

**Visibility Enforcement:**

```python
# In sync_service.py
def set_document_visibility(doc, data_source):
    if data_source.data_classification == "public":
        doc.visibility_level = "public"
        doc.institution_id = None
    elif data_source.data_classification == "educational":
        doc.visibility_level = "national"
        doc.institution_id = None
    elif data_source.data_classification == "confidential":
        doc.visibility_level = "ministry_only"
        doc.institution_id = data_source.institution_id
    elif data_source.data_classification == "institutional":
        doc.visibility_level = "institutional"
        doc.institution_id = data_source.institution_id
```

#### **3. Database Migration**

```python
# alembic/versions/add_data_source_workflow.py
def upgrade():
    op.add_column('external_data_sources',
        sa.Column('institution_id', sa.Integer(), nullable=True))
    op.add_column('external_data_sources',
        sa.Column('requested_by_user_id', sa.Integer(), nullable=True))
    op.add_column('external_data_sources',
        sa.Column('approved_by_user_id', sa.Integer(), nullable=True))
    op.add_column('external_data_sources',
        sa.Column('request_status', sa.String(20), default='pending'))
    op.add_column('external_data_sources',
        sa.Column('data_classification', sa.String(20), nullable=True))
    # ... more columns
```

---

## 📊 Implementation Roadmap

### **Phase 1: Request System** (Estimated: 2-3 days)

**Day 1: Backend**

- [ ] Database migration (add workflow fields)
- [ ] New API endpoints (request, my-requests, pending)
- [ ] Request submission logic
- [ ] Test connection enhancement

**Day 2: Frontend**

- [ ] DataSourceRequestPage component
- [ ] Form with validation
- [ ] Test connection button
- [ ] Classification dropdown (ministry only)

**Day 3: Frontend**

- [ ] MyDataSourceRequestsPage component
- [ ] Request list with status badges
- [ ] Rejection reason display
- [ ] Resubmit functionality

### **Phase 2: Approval System** (Estimated: 2-3 days)

**Day 1: Backend**

- [ ] Approval/rejection endpoints
- [ ] Notification integration
- [ ] Auto-sync on approval
- [ ] Audit logging

**Day 2-3: Frontend**

- [ ] DataSourceApprovalPage (Developer)
- [ ] Pending requests list
- [ ] Approve/reject actions
- [ ] Request details modal
- [ ] Sync trigger integration

### **Phase 3: Visibility Enforcement** (Estimated: 2 days)

**Day 1: Backend**

- [ ] Update sync service with visibility logic
- [ ] Document classification on sync
- [ ] Access control in RAG queries
- [ ] Testing visibility rules

**Day 2: Testing**

- [ ] End-to-end testing
- [ ] Role-based access testing
- [ ] Cross-ministry visibility testing
- [ ] Security audit

### **Phase 4: Polish & Monitoring** (Estimated: 1-2 days)

- [ ] Sync monitoring dashboard
- [ ] Error handling improvements
- [ ] User documentation
- [ ] Admin guide

**Total Estimated Time: 7-10 days**

---

## 🔐 Security Considerations

### **Already Implemented:**

✅ Password encryption (Fernet)
✅ Connection timeout (10 seconds)
✅ Developer-only access to current endpoints
✅ SQL injection prevention (parameterized queries)

### **Need to Implement:**

- [ ] Request rate limiting
- [ ] Connection pool management
- [ ] Audit trail for all operations
- [ ] IP whitelisting for external DBs
- [ ] Encrypted connection (SSL/TLS)
- [ ] Credential rotation support

---

## 🎯 Key Decisions Needed Before Implementation

### **1. Cross-Ministry Visibility**

**Question:** Can Ministry of Health see Ministry of Education's "Educational" data?

**Option A:** Yes (Collaboration)

- Promotes inter-ministry collaboration
- Useful for policy alignment
- More complex access control

**Option B:** No (Isolation)

- Simpler security model
- Each ministry isolated
- Clearer data ownership

**Recommendation:** Start with Option B (isolation), add Option A later if needed

### **2. Developer Access Level**

**Question:** Should Developer see ALL data or only approved sources?

**Option A:** ALL data (System Admin)

- Full system visibility
- Better for debugging
- Security concern

**Option B:** Only approved sources

- More secure
- Follows principle of least privilege
- May limit troubleshooting

**Recommendation:** Option A (ALL data) - Developer needs full visibility for system management

### **3. Auto-Sync on Approval**

**Question:** Start sync immediately after approval or wait for manual trigger?

**Option A:** Auto-sync

- Faster data availability
- Better UX
- May cause load issues

**Option B:** Manual trigger

- More control
- Can schedule syncs
- Requires extra step

**Recommendation:** Option A (Auto-sync) with option to disable in settings

---

## 📝 Summary

### **What Exists:**

✅ Complete backend infrastructure
✅ Database models
✅ API endpoints (developer-only)
✅ Sync service
✅ Password encryption
✅ Connection testing

### **What's Missing:**

❌ Frontend UI (all pages)
❌ Request/approval workflow
❌ Visibility controls
❌ Notifications
❌ Role-based access (ministry/university admins)

### **Next Steps:**

1. Review and approve this plan
2. Make key decisions (cross-ministry visibility, etc.)
3. Start Phase 1: Request System
4. Build frontend pages
5. Implement approval workflow
6. Add visibility controls
7. Test end-to-end
8. Deploy

**Status:** ✅ Backend Ready | ❌ Frontend Not Started | 📋 Plan Complete

**Estimated Total Implementation Time:** 7-10 days for complete system
