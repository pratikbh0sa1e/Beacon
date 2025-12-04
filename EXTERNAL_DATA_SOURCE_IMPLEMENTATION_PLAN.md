# External Data Source Implementation Plan

## Overview

Request-based system for connecting external databases (ministry and university databases) with flexible visibility controls and developer approval workflow.

## Selected Options & Decisions

### 1. **Request System: Option 1 (Request & Approval)**

- Ministry Admin and University Admin can submit connection requests
- Developer reviews and approves/rejects all requests
- Includes audit trail and notifications

### 2. **Who Can Request:**

- ✅ **Ministry Admin** (any ministry - MoE, Health, Finance, etc.)
- ✅ **University Admin** (their institution's database)
- ✅ **Developer** (can approve/reject all requests)

### 3. **Visibility Model:**

#### **For Ministry Admin - Flexible with Dropdown:**

Ministry admin selects data classification when requesting:

| Classification   | Visibility                     | Who Can See                                   |
| ---------------- | ------------------------------ | --------------------------------------------- |
| **Public**       | `visibility = "public"`        | Everyone (all users, public viewers)          |
| **Educational**  | `visibility = "national"`      | All universities + All ministries (no public) |
| **Confidential** | `visibility = "ministry_only"` | Only that ministry + Developer                |

#### **For University Admin - No Dropdown (Option A):**

- Always `visibility = "institutional"`
- Always `institution_id = their_university_id`
- Data only visible to their institution
- Simpler, safer, prevents accidental data exposure

### 4. **Cross-Ministry Visibility:**

**Pending Decision - Need to confirm:**

- [ ] **Option A:** All ministries can see each other's "Educational" data (collaboration)
- [ ] **Option B:** Each ministry isolated (only their own data)

### 5. **Developer Access:**

**Pending Decision - Need to confirm:**

- [ ] **Option A:** Developer sees ALL data from ALL ministries (system admin)
- [ ] **Option B:** Developer only sees approved data sources

---

## Database Schema Changes

### **1. Add to `external_data_sources` table:**

```sql
ALTER TABLE external_data_sources ADD COLUMN IF NOT EXISTS institution_id INTEGER REFERENCES institutions(id);
ALTER TABLE external_data_sources ADD COLUMN IF NOT EXISTS requested_by_user_id INTEGER REFERENCES users(id);
ALTER TABLE external_data_sources ADD COLUMN IF NOT EXISTS approved_by_user_id INTEGER REFERENCES users(id);
ALTER TABLE external_data_sources ADD COLUMN IF NOT EXISTS request_status VARCHAR(20) DEFAULT 'pending';
ALTER TABLE external_data_sources ADD COLUMN IF NOT EXISTS data_classification VARCHAR(20);
ALTER TABLE external_data_sources ADD COLUMN IF NOT EXISTS request_notes TEXT;
ALTER TABLE external_data_sources ADD COLUMN IF NOT EXISTS rejection_reason TEXT;
ALTER TABLE external_data_sources ADD COLUMN IF NOT EXISTS requested_at TIMESTAMP DEFAULT NOW();
ALTER TABLE external_data_sources ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP;

-- Indexes
CREATE INDEX idx_external_data_sources_institution ON external_data_sources(institution_id);
CREATE INDEX idx_external_data_sources_status ON external_data_sources(request_status);
CREATE INDEX idx_external_data_sources_requester ON external_data_sources(requested_by_user_id);
```

### **2. Field Definitions:**

| Field                  | Type         | Description                     | Values                                                   |
| ---------------------- | ------------ | ------------------------------- | -------------------------------------------------------- |
| `institution_id`       | Integer (FK) | Links to ministry or university | NULL for legacy, ID for new requests                     |
| `requested_by_user_id` | Integer (FK) | User who submitted request      | User ID                                                  |
| `approved_by_user_id`  | Integer (FK) | Developer who approved          | User ID or NULL                                          |
| `request_status`       | String       | Current status                  | `pending`, `approved`, `rejected`                        |
| `data_classification`  | String       | Visibility level                | `public`, `educational`, `confidential`, `institutional` |
| `request_notes`        | Text         | Requester's notes               | Free text                                                |
| `rejection_reason`     | Text         | Why rejected                    | Free text (if rejected)                                  |
| `requested_at`         | Timestamp    | When requested                  | Auto timestamp                                           |
| `approved_at`          | Timestamp    | When approved/rejected          | Timestamp or NULL                                        |

---

## API Endpoints

### **Request Management:**

#### **1. Submit Request**

```
POST /api/data-sources/request
Body: {
  name, ministry_name, description,
  host, port, database_name, username, password,
  table_name, file_column, filename_column,
  data_classification,  // Only for ministry admin
  request_notes
}
Access: ministry_admin, university_admin
```

#### **2. Get My Requests**

```
GET /api/data-sources/my-requests
Access: ministry_admin, university_admin
Returns: List of user's submitted requests with status
```

#### **3. Get Pending Requests (Developer)**

```
GET /api/data-sources/requests/pending
Access: developer only
Returns: All pending requests for approval
```

#### **4. Approve Request**

```
POST /api/data-sources/requests/{id}/approve
Access: developer only
Action:
  - Test connection
  - Update status to 'approved'
  - Enable sync
  - Send notification to requester
```

#### **5. Reject Request**

```
POST /api/data-sources/requests/{id}/reject
Body: { rejection_reason }
Access: developer only
Action:
  - Update status to 'rejected'
  - Store rejection reason
  - Send notification to requester
```

#### **6. Test Connection (Before Submit)**

```
POST /api/data-sources/test-connection
Body: { host, port, database_name, username, password }
Access: ministry_admin, university_admin, developer
Returns: { status: "success" | "failed", message }
```

---

## Frontend Components

### **1. Data Source Request Form**

**Location:** `frontend/src/pages/admin/DataSourceRequestPage.jsx`

**Access:** Ministry Admin, University Admin

**Features:**

- Database connection form
- Test connection button
- Data classification dropdown (ministry only)
- Request notes textarea
- Submit button

**Form Fields:**

**Common Fields:**

- Data Source Name
- Description
- Database Host
- Database Port
- Database Name
- Username
- Password (encrypted)
- Table Name
- File Column Name
- Filename Column Name
- Request Notes

**Ministry Admin Only:**

- Data Classification Dropdown:
  - Public (Everyone)
  - Educational (Universities + Ministries)
  - Confidential (Ministry Only)

**University Admin:**

- Auto-set: `data_classification = "institutional"`
- Show info: "Data will be visible only to your institution"

### **2. My Requests Page**

**Location:** `frontend/src/pages/admin/MyDataSourceRequestsPage.jsx`

**Access:** Ministry Admin, University Admin

**Features:**

- List of submitted requests
- Status badges (Pending/Approved/Rejected)
- View details
- Rejection reason (if rejected)
- Resubmit option (for rejected)

### **3. Request Approval Dashboard**

**Location:** `frontend/src/pages/admin/DataSourceApprovalPage.jsx`

**Access:** Developer Only

**Features:**

- List of pending requests
- View request details
- Test connection button
- Approve/Reject buttons
- Rejection reason textarea
- Request history

**Tabs:**

- Pending Requests
- Approved Requests
- Rejected Requests
- All Requests

### **4. Active Data Sources List**

**Location:** `frontend/src/pages/admin/DataSourcesPage.jsx`

**Access:** Developer Only

**Features:**

- List of approved & active data sources
- Sync status
- Manual sync trigger
- Edit/Delete options
- Sync logs

---

## Visibility Enforcement

### **Document Query Filters:**

When syncing documents from external data sources, set:

```python
# For Ministry Data Sources
if data_classification == "public":
    document.visibility = "public"
    document.institution_id = None

elif data_classification == "educational":
    document.visibility = "national"
    document.institution_id = None

elif data_classification == "confidential":
    document.visibility = "ministry_only"
    document.institution_id = ministry_institution_id

# For University Data Sources
elif data_classification == "institutional":
    document.visibility = "institutional"
    document.institution_id = university_institution_id
```

### **Access Control in Document Queries:**

```python
# When user queries documents
if user.role == "developer":
    # See all documents
    pass

elif user.role == "ministry_admin":
    # See: public + national + their ministry's confidential
    filter(
        (visibility == "public") |
        (visibility == "national") |
        (visibility == "ministry_only" AND institution_id == user.institution_id)
    )

elif user.role == "university_admin":
    # See: public + national + their institution's
    filter(
        (visibility == "public") |
        (visibility == "national") |
        (visibility == "institutional" AND institution_id == user.institution_id)
    )

elif user.role == "student":
    # See: public + national + their institution's
    filter(
        (visibility == "public") |
        (visibility == "national") |
        (visibility == "institutional" AND institution_id == user.institution_id)
    )

elif user.role == "public_viewer":
    # See: public only
    filter(visibility == "public")
```

---

## Notification System

### **Notifications to Send:**

1. **New Request Submitted:**

   - To: All Developers
   - Message: "New data source connection request from {user_name} ({institution_name})"
   - Action: Link to approval dashboard

2. **Request Approved:**

   - To: Requester
   - Message: "Your data source request '{name}' has been approved. Sync will start automatically."
   - Action: Link to data sources page

3. **Request Rejected:**

   - To: Requester
   - Message: "Your data source request '{name}' was rejected. Reason: {rejection_reason}"
   - Action: Link to resubmit form

4. **Sync Completed:**
   - To: Requester + Developer
   - Message: "Data source '{name}' sync completed. {count} documents synced."
   - Action: Link to synced documents

---

## Security Considerations

### **1. Password Encryption:**

- All database passwords encrypted before storage
- Use existing `ExternalDBConnector.encrypt_password()` method
- Never return passwords in API responses

### **2. Connection Testing:**

- Test connection before approval
- Validate credentials
- Check table/column existence
- Timeout after 10 seconds

### **3. Access Control:**

- Ministry admin can only see their ministry's requests
- University admin can only see their university's requests
- Developer can see all requests
- Enforce institution_id checks

### **4. Audit Trail:**

- Log all request submissions
- Log all approvals/rejections
- Log who approved/rejected
- Track sync operations

---

## UI/UX Flow

### **Ministry Admin Flow:**

```
1. Navigate to "Data Sources" → "Request Connection"
2. Fill form with database details
3. Select data classification (Public/Educational/Confidential)
4. Click "Test Connection" (optional)
5. Add request notes
6. Submit request
7. See "Request Submitted" confirmation
8. Navigate to "My Requests" to track status
9. Receive notification when approved/rejected
10. If approved, data syncs automatically
```

### **University Admin Flow:**

```
1. Navigate to "Data Sources" → "Request Connection"
2. Fill form with database details
3. See info: "Data will be institutional only"
4. Click "Test Connection" (optional)
5. Add request notes
6. Submit request
7. See "Request Submitted" confirmation
8. Navigate to "My Requests" to track status
9. Receive notification when approved/rejected
10. If approved, data syncs automatically
```

### **Developer Flow:**

```
1. Receive notification of new request
2. Navigate to "Data Source Approvals"
3. Review request details
4. Click "Test Connection" to verify
5. If valid:
   - Click "Approve"
   - Sync starts automatically
   - Requester notified
6. If invalid:
   - Click "Reject"
   - Enter rejection reason
   - Requester notified
```

---

## Testing Checklist

- [ ] Ministry admin can submit request with classification
- [ ] University admin can submit request (no classification)
- [ ] Test connection works before submit
- [ ] Developer receives notification
- [ ] Developer can approve request
- [ ] Developer can reject request with reason
- [ ] Approved source starts syncing
- [ ] Documents get correct visibility
- [ ] Ministry admin sees their requests only
- [ ] University admin sees their requests only
- [ ] Developer sees all requests
- [ ] Notifications sent correctly
- [ ] Passwords encrypted in database
- [ ] Access control enforced on documents
- [ ] Sync logs created properly

---

## Future Enhancements

- [ ] Edit pending requests
- [ ] Cancel pending requests
- [ ] Bulk approve/reject
- [ ] Request templates
- [ ] Connection health monitoring
- [ ] Auto-retry failed syncs
- [ ] Email notifications
- [ ] Request comments/discussion
- [ ] Approval workflow (multi-level)
- [ ] Data source analytics

---

## Implementation Priority

### **Phase 1: Core Request System** (Week 1)

1. Database migration
2. Backend API endpoints
3. Request form (frontend)
4. My Requests page (frontend)

### **Phase 2: Approval System** (Week 2)

1. Approval dashboard (frontend)
2. Approve/reject logic (backend)
3. Notification system
4. Test connection feature

### **Phase 3: Visibility Enforcement** (Week 3)

1. Update document sync logic
2. Update document query filters
3. Access control testing
4. End-to-end testing

---

## Notes

- This implementation will be done AFTER generalizing ministry roles
- Requires `MINISTRY_ADMIN` → `ministry_admin` role migration first
- Requires institution type support (ministry vs university)
- Backward compatible with existing data sources (status = 'approved' by default)

---

## Pending Decisions (To be confirmed before implementation)

1. **Cross-ministry visibility:** Can Ministry of Health see MoE's "Educational" data?
2. **Developer access:** Should developer see ALL data or only approved sources?
3. **Resubmit rejected requests:** Allow editing and resubmitting?
4. **Auto-sync on approval:** Start sync immediately or wait for manual trigger?

---

**Status:** Planning Complete - Ready for Implementation After Ministry Generalization

**Last Updated:** December 3, 2024
