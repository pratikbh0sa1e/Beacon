# Document Approval Tabs - COMPLETE ✅

## Implementation Summary

I've successfully implemented the backend endpoints and updated the frontend to show approved and rejected documents in separate tabs.

---

## Backend Changes ✅

### File: `backend/routers/approval_router.py`

**Added Two New Endpoints**:

### 1. GET `/approvals/documents/approved`

**Purpose**: Get all approved documents based on user role

**Role-Based Filtering**:

- **Developer**: Sees all approved documents
- **MoE Admin**: Sees restricted and public approved documents
- **University Admin**: Sees institution-only and public approved documents from their institution

**Response Format**:

```json
{
  "approved_documents": [
    {
      "id": 123,
      "filename": "policy.pdf",
      "file_type": "pdf",
      "visibility_level": "public",
      "uploaded_at": "2024-01-15T10:00:00Z",
      "approved_at": "2024-01-15T11:00:00Z",
      "uploader": {
        "id": 45,
        "name": "John Doe",
        "email": "john@example.com"
      },
      "approver": {
        "id": 12,
        "name": "Admin User",
        "role": "university_admin"
      },
      "institution_id": 5
    }
  ]
}
```

**Database Query**:

```python
# Base query
query = db.query(Document).filter(Document.approval_status == "approved")

# Role-based filtering
if current_user.role == "developer":
    pass  # See all
elif current_user.role == "moe_admin":
    query = query.filter(Document.visibility_level.in_(["restricted", "public"]))
elif current_user.role == "university_admin":
    query = query.filter(
        Document.institution_id == current_user.institution_id,
        Document.visibility_level.in_(["institution_only", "public"])
    )

# Order by approval date
documents = query.order_by(Document.approved_at.desc()).all()
```

---

### 2. GET `/approvals/documents/rejected`

**Purpose**: Get all rejected documents based on user role

**Role-Based Filtering**: Same as approved documents

**Response Format**:

```json
{
  "rejected_documents": [
    {
      "id": 124,
      "filename": "invalid.pdf",
      "file_type": "pdf",
      "visibility_level": "public",
      "uploaded_at": "2024-01-15T10:00:00Z",
      "rejected_at": "2024-01-15T11:30:00Z",
      "uploader": {
        "id": 46,
        "name": "Jane Smith",
        "email": "jane@example.com"
      },
      "rejector": {
        "id": 12,
        "name": "Admin User",
        "role": "university_admin"
      },
      "institution_id": 5
    }
  ]
}
```

**Database Query**:

```python
# Base query
query = db.query(Document).filter(Document.approval_status == "rejected")

# Same role-based filtering as approved
# Order by rejection date
documents = query.order_by(Document.approved_at.desc()).all()
```

**Note**: The `approved_at` field stores both approval and rejection timestamps.

---

## Frontend Changes ✅

### 1. API Service Updated

**File**: `frontend/src/services/api.js`

**Added**:

```javascript
export const approvalAPI = {
  getPendingDocuments: () => api.get("/approvals/documents/pending"),
  getApprovedDocuments: () => api.get("/approvals/documents/approved"), // NEW
  getRejectedDocuments: () => api.get("/approvals/documents/rejected"), // NEW
  approveDocument: (docId, notes) =>
    api.post(`/approvals/documents/approve/${docId}`, { notes }),
  rejectDocument: (docId, notes) =>
    api.post(`/approvals/documents/reject/${docId}`, { notes }),
  getDocumentHistory: (docId) =>
    api.get(`/approvals/documents/history/${docId}`),
};
```

---

### 2. Document Approvals Page Updated

**File**: `frontend/src/pages/admin/DocumentApprovalsPage.jsx`

**Updated Fetch Function**:

```javascript
const fetchDocuments = async () => {
  setLoading(true);
  try {
    let response;
    if (activeTab === "pending") {
      response = await approvalAPI.getPendingDocuments();
      setDocuments(response.data.pending_documents || []);
    } else if (activeTab === "approved") {
      response = await approvalAPI.getApprovedDocuments();
      setDocuments(response.data.approved_documents || []);
    } else if (activeTab === "rejected") {
      response = await approvalAPI.getRejectedDocuments();
      setDocuments(response.data.rejected_documents || []);
    }
  } catch (error) {
    console.error("Error fetching documents:", error);
    toast.error("Failed to load documents");
  } finally {
    setLoading(false);
  }
};
```

**Updated Tab Content**:

- **Approved Tab**: Shows approved documents with green checkmark icon
- **Rejected Tab**: Shows rejected documents with red X icon
- Both tabs show:
  - Uploader information
  - Approver/Rejector information
  - Approval/Rejection timestamp
  - View button to see document details

---

## UI Features

### Approved Documents Tab

**Visual Indicators**:

- ✅ Green checkmark icon
- ✅ Green border on hover
- ✅ "Approved" badge (green)
- ✅ Shows approver name and role
- ✅ Shows approval timestamp

**Card Layout**:

```
┌─────────────────────────────────────────┐
│ ✓ policy.pdf                            │
│   [PUBLIC] [PDF] [Approved]             │
│   👤 Uploaded by John Doe               │
│   ✓ Approved by Admin User              │
│   📅 2 hours ago                        │
│                            [View]       │
└─────────────────────────────────────────┘
```

---

### Rejected Documents Tab

**Visual Indicators**:

- ✗ Red X icon
- ✗ Red border on hover
- ✗ "Rejected" badge (red)
- ✗ Shows rejector name and role
- ✗ Shows rejection timestamp

**Card Layout**:

```
┌─────────────────────────────────────────┐
│ ✗ invalid.pdf                           │
│   [PUBLIC] [PDF] [Rejected]             │
│   👤 Uploaded by Jane Smith             │
│   ✗ Rejected by Admin User              │
│   📅 1 day ago                          │
│                            [View]       │
└─────────────────────────────────────────┘
```

---

## Complete Tab System

### Pending Tab (Yellow)

- ⏰ Clock icon
- Shows documents awaiting approval
- Actions: Review, Approve, Reject

### Approved Tab (Green)

- ✓ Checkmark icon
- Shows approved documents
- Actions: View only

### Rejected Tab (Red)

- ✗ X icon
- Shows rejected documents
- Actions: View only

---

## Role-Based Access

All three tabs respect role-based permissions:

| Role                 | Can See                                                      |
| -------------------- | ------------------------------------------------------------ |
| **Developer**        | All documents (pending, approved, rejected)                  |
| **MoE Admin**        | Restricted and public documents                              |
| **University Admin** | Institution-only and public documents from their institution |
| **Others**           | No access (403 error)                                        |

---

## Testing Checklist

### Backend ✅

- [x] GET `/approvals/documents/approved` endpoint created
- [x] GET `/approvals/documents/rejected` endpoint created
- [x] Role-based filtering implemented
- [x] Proper response format
- [x] Includes uploader and approver/rejector info
- [x] Ordered by approval/rejection date

### Frontend ✅

- [x] API service updated with new endpoints
- [x] Fetch function calls correct endpoint per tab
- [x] Approved tab shows approved documents
- [x] Rejected tab shows rejected documents
- [x] Visual indicators (icons, colors, badges)
- [x] Approver/rejector information displayed
- [x] Timestamps formatted correctly
- [x] Empty states for no documents
- [x] Loading states work
- [x] Search and filters work on all tabs

### Integration ✅

- [x] Tab switching fetches correct data
- [x] Documents display with correct status
- [x] Role-based filtering works
- [x] View button navigates to document detail
- [x] No errors in console

---

## Database Schema Reference

**Documents Table Fields Used**:

- `approval_status`: "pending" | "approved" | "rejected"
- `approved_by`: User ID of approver/rejector
- `approved_at`: Timestamp of approval/rejection
- `visibility_level`: Document visibility level
- `institution_id`: Institution association

**Note**: The `approved_at` field is used for both approvals and rejections. The `approval_status` field determines which it is.

---

## API Endpoints Summary

| Endpoint                            | Method | Purpose                | Response Key         |
| ----------------------------------- | ------ | ---------------------- | -------------------- |
| `/approvals/documents/pending`      | GET    | Get pending documents  | `pending_documents`  |
| `/approvals/documents/approved`     | GET    | Get approved documents | `approved_documents` |
| `/approvals/documents/rejected`     | GET    | Get rejected documents | `rejected_documents` |
| `/approvals/documents/approve/{id}` | POST   | Approve a document     | `document`           |
| `/approvals/documents/reject/{id}`  | POST   | Reject a document      | `document`           |
| `/approvals/documents/history/{id}` | GET    | Get approval history   | `history`            |

---

## Example Usage

### Approve a Document:

1. Go to Pending tab
2. Click "Approve" on a document
3. Add optional notes
4. Confirm approval
5. Document moves to Approved tab

### View Approved Documents:

1. Click "Approved" tab
2. See all approved documents
3. View approver and timestamp
4. Click "View" to see details

### View Rejected Documents:

1. Click "Rejected" tab
2. See all rejected documents
3. View rejector and timestamp
4. Click "View" to see details

---

## Summary

✅ **Backend**: Two new endpoints added with role-based filtering
✅ **Frontend**: Tabs fully functional with real data
✅ **UI**: Visual indicators for each status
✅ **Integration**: Complete workflow from pending → approved/rejected

**All three tabs are now fully functional!** 🎉

Users can:

- View pending documents and approve/reject them
- View all approved documents with approval details
- View all rejected documents with rejection details
- Search and filter across all tabs
- See role-appropriate documents only

The document approval system is now **COMPLETE**! ✅
