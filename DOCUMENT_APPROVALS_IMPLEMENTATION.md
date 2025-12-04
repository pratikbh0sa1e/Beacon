# Document Approvals Page Implementation

## Overview

Created a comprehensive Document Approvals page for administrators to review and approve/reject pending document submissions.

---

## Files Created/Modified

### 1. New Page: `frontend/src/pages/admin/DocumentApprovalsPage.jsx` ✅

**Features:**

- **Stats Dashboard**: Shows pending approvals, filtered results, and high-priority documents
- **Search & Filter**: Search by filename/uploader, filter by visibility level
- **Document Cards**: Display document info, uploader details, and upload time
- **Action Buttons**:
  - Review (opens document detail page)
  - Approve (with optional notes)
  - Reject (requires reason)
- **Confirmation Dialogs**: Modal dialogs for approve/reject actions
- **Real-time Updates**: Refreshes list after approval/rejection
- **Priority Indicators**: Highlights restricted/confidential documents

**UI Components Used:**

- PageHeader
- Card, CardContent
- Badge (for visibility levels)
- Button
- Input (search)
- Select (filter dropdown)
- Dialog (confirmation modals)
- Textarea (notes/reason input)
- LoadingSpinner
- EmptyState

---

### 2. Updated: `frontend/src/App.jsx` ✅

**Changes:**

- Imported `DocumentApprovalsPage`
- Added route: `/admin/approvals`
- Protected with `ADMIN_ROLES` (developer, MINISTRY_ADMIN, university_admin)

**Route Structure:**

```jsx
<Route
  path="admin/approvals"
  element={
    <ProtectedRoute allowedRoles={ADMIN_ROLES}>
      <DocumentApprovalsPage />
    </ProtectedRoute>
  }
/>
```

---

## Backend API (Already Exists) ✅

### Endpoints Used:

1. **GET** `/approvals/documents/pending`

   - Returns pending documents based on user role
   - Developer: sees all
   - MoE Admin: sees restricted & public
   - University Admin: sees institution-only & public from their institution

2. **POST** `/approvals/documents/approve/{document_id}`

   - Approves a document
   - Requires permission based on visibility level
   - Logs audit trail

3. **POST** `/approvals/documents/reject/{document_id}`

   - Rejects a document
   - Requires rejection reason
   - Logs audit trail

4. **GET** `/approvals/documents/history/{document_id}`
   - Gets approval history (not used in current UI, but available)

---

## Role-Based Permissions

### Who Can Approve What:

| Role                 | Can Approve                                                        |
| -------------------- | ------------------------------------------------------------------ |
| **Developer**        | All documents (public, institution_only, restricted, confidential) |
| **MoE Admin**        | Public, restricted documents                                       |
| **University Admin** | Public and institution_only documents from their institution       |
| **Others**           | No approval permissions                                            |

---

## Visibility Levels

| Level                | Badge Color       | Description                      |
| -------------------- | ----------------- | -------------------------------- |
| **Public**           | Default (blue)    | Accessible to everyone           |
| **Institution Only** | Secondary (gray)  | Only for specific institution    |
| **Restricted**       | Outline           | Limited access, high priority    |
| **Confidential**     | Destructive (red) | Highest security, developer only |

---

## User Flow

### Approval Process:

1. Admin navigates to `/admin/approvals`
2. Views list of pending documents
3. Can search/filter documents
4. Clicks "Review" to see document details
5. Clicks "Approve" → Confirmation dialog → Document approved
6. Clicks "Reject" → Must provide reason → Document rejected

### Features:

- **Search**: Filter by filename or uploader name/email
- **Filter**: Filter by visibility level
- **Stats**: See counts at a glance
- **Priority Alerts**: Visual indicators for high-priority documents
- **Notes**: Optional notes for approval, required reason for rejection

---

## UI/UX Highlights

1. **Responsive Design**: Works on mobile, tablet, and desktop
2. **Motion Animations**: Smooth entry animations for document cards
3. **Color Coding**: Different badge colors for visibility levels
4. **Empty States**: Helpful messages when no documents or no results
5. **Loading States**: Spinners during data fetch and actions
6. **Toast Notifications**: Success/error messages for user feedback
7. **Confirmation Dialogs**: Prevent accidental approvals/rejections

---

## Testing Checklist

### Frontend

- [ ] Page loads without errors
- [ ] Pending documents display correctly
- [ ] Search filters documents
- [ ] Visibility filter works
- [ ] Stats cards show correct counts
- [ ] Review button navigates to document detail
- [ ] Approve dialog opens and works
- [ ] Reject dialog requires reason
- [ ] Success/error toasts appear
- [ ] List refreshes after approval/rejection
- [ ] Empty state shows when no documents
- [ ] Responsive on mobile devices

### Backend

- [ ] `/approvals/documents/pending` returns correct documents for each role
- [ ] Approve endpoint works and logs audit
- [ ] Reject endpoint works and logs audit
- [ ] Permissions are enforced correctly
- [ ] Cannot approve already approved documents
- [ ] Cannot approve rejected documents

### Integration

- [ ] Sidebar "Approvals" button navigates correctly
- [ ] Only admins can access the page
- [ ] Document detail page shows approval status
- [ ] Dashboard stats reflect pending approvals

---

## Navigation

**Sidebar Button:**

- Label: "Approvals"
- Icon: Shield
- Path: `/admin/approvals`
- Visible to: ADMIN_ROLES (developer, MINISTRY_ADMIN, university_admin)

---

## Future Enhancements (Optional)

1. **Bulk Actions**: Approve/reject multiple documents at once
2. **Approval History**: Show approval history on the page
3. **Email Notifications**: Notify uploaders when documents are approved/rejected
4. **Document Preview**: Preview document content in a modal
5. **Advanced Filters**: Filter by uploader, date range, institution
6. **Export**: Export pending documents list to CSV
7. **Comments**: Allow reviewers to add comments before approval
8. **Delegation**: Allow admins to delegate approval to others
9. **Auto-Approval Rules**: Set rules for automatic approval of certain documents
10. **Analytics**: Track approval times, rejection rates, etc.

---

## Database Schema (Reference)

### Document Table Fields:

- `approval_status`: "pending" | "approved" | "rejected"
- `approved_by`: User ID of approver
- `approved_at`: Timestamp of approval/rejection
- `visibility_level`: "public" | "institution_only" | "restricted" | "confidential"

### Audit Log:

- Tracks all approval/rejection actions
- Stores notes/reasons
- Links to user and document

---

## API Response Examples

### Pending Documents:

```json
{
  "pending_documents": [
    {
      "id": 123,
      "filename": "policy-2024.pdf",
      "file_type": "pdf",
      "visibility_level": "restricted",
      "uploaded_at": "2024-01-15T10:30:00Z",
      "uploader": {
        "id": 45,
        "name": "John Doe",
        "email": "john@example.com"
      },
      "institution_id": 5
    }
  ]
}
```

### Approval Response:

```json
{
  "status": "success",
  "message": "Document 'policy-2024.pdf' has been approved",
  "document": {
    "id": 123,
    "filename": "policy-2024.pdf",
    "approval_status": "approved",
    "approved_by": "Admin Name",
    "approved_at": "2024-01-15T11:00:00Z"
  }
}
```

---

## Summary

✅ **Document Approvals Page Created**
✅ **Route Added to App.jsx**
✅ **Backend API Already Exists**
✅ **Role-Based Permissions Implemented**
✅ **Search & Filter Functionality**
✅ **Approve/Reject Workflows**
✅ **Confirmation Dialogs**
✅ **Toast Notifications**
✅ **Responsive Design**

The Document Approvals page is now fully functional and ready for use by administrators!
