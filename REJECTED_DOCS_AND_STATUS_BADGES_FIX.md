# ✅ Rejected Documents & Status Badges Fix

## 🐛 Problems Fixed

### 1. Rejected Documents Not Showing in Approvals Page

**Problem:** Rejected documents were filtered out by the backend, so they didn't appear in the "Rejected" tab.

**Root Cause:** The approval status filter only included `["approved", "pending", "under_review", "changes_requested"]` but not `"rejected"`.

### 2. No Status Badge in Document Explorer

**Problem:** Users couldn't see the approval status of documents in the document explorer grid/list view.

**Suggestion:** Adding status badges would help users quickly identify document status without clicking.

---

## ✅ Solutions Implemented

### 1. Backend: Include Rejected Documents for Admins

**File:** `backend/routers/document_router.py`

**Before:**

```python
elif current_user.role in ["ministry_admin", "university_admin"]:
    query = query.filter(
        or_(
            Document.approval_status.in_(["approved", "pending", "under_review", "changes_requested"]),
            Document.uploader_id == current_user.id
        )
    )
```

**After:**

```python
elif current_user.role in ["ministry_admin", "university_admin"]:
    query = query.filter(
        or_(
            Document.approval_status.in_(["approved", "pending", "under_review", "changes_requested", "rejected", "archived", "flagged"]),
            Document.uploader_id == current_user.id
        )
    )
```

**What Changed:**

- ✅ Added `"rejected"` to the list of visible statuses
- ✅ Added `"archived"` and `"flagged"` for completeness
- ✅ Admins can now see all document statuses

---

### 2. Backend: Return approval_status in Document List

**File:** `backend/routers/document_router.py`

**Added to response:**

```python
documents.append({
    "id": doc.id,
    "title": meta.title if meta else doc.filename,
    "description": display_description,
    "category": meta.document_type if meta else "Uncategorized",
    "visibility": doc.visibility_level,
    "download_allowed": doc.download_allowed,
    "approval_status": doc.approval_status,  # ✅ Added
    "department": meta.department if meta else "Unknown",
    # ... rest of fields
})
```

**Why:** Frontend needs approval_status to display badges in document explorer.

---

### 3. Frontend: Add Status Badge to Document Explorer

**File:** `frontend/src/pages/documents/DocumentExplorerPage.jsx`

**Added Status Badge:**

```jsx
<div className="flex flex-col gap-2">
  <Badge variant="outline">{doc.category}</Badge>

  {/* ✅ NEW: Approval Status Badge */}
  {doc.approval_status && (
    <Badge
      className={
        doc.approval_status === "approved"
          ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
          : doc.approval_status === "pending"
          ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
          : doc.approval_status === "rejected"
          ? "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
          : doc.approval_status === "draft"
          ? "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200"
          : "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
      }
    >
      {doc.approval_status.replace("_", " ").toUpperCase()}
    </Badge>
  )}
</div>
```

**Badge Colors:**

- 🟢 **Green** - APPROVED
- 🟡 **Yellow** - PENDING
- 🔴 **Red** - REJECTED
- ⚪ **Gray** - DRAFT
- 🔵 **Blue** - Other statuses (under_review, changes_requested, etc.)

**Location:** Top-left of each document card, below the category badge

---

## 📊 Visual Changes

### Document Explorer - Before:

```
┌─────────────────────────────┐
│ [Category Badge]      [⭐]  │
│                             │
│ Document Title              │
│ Description...              │
└─────────────────────────────┘
```

### Document Explorer - After:

```
┌─────────────────────────────┐
│ [Category Badge]      [⭐]  │
│ [APPROVED Badge]            │  ← NEW!
│                             │
│ Document Title              │
│ Description...              │
└─────────────────────────────┘
```

---

## 🎯 User Benefits

### For Admins:

1. ✅ Can now see rejected documents in Approvals page
2. ✅ Can review rejection history
3. ✅ Can see all document statuses at a glance

### For All Users:

1. ✅ Status badge shows approval state without clicking
2. ✅ Color-coded for quick recognition
3. ✅ Consistent with Approvals page design
4. ✅ Works in both light and dark mode

---

## 🔍 Status Badge Visibility

### Who Sees Status Badges:

| User Role            | Sees Status Badge | Which Statuses                              |
| -------------------- | ----------------- | ------------------------------------------- |
| **Developer**        | ✅ Yes            | All statuses                                |
| **MoE Admin**        | ✅ Yes            | All statuses they can access                |
| **University Admin** | ✅ Yes            | All statuses from their institution         |
| **Document Officer** | ✅ Yes            | Approved + their own drafts                 |
| **Student**          | ✅ Yes            | Only approved (they only see approved docs) |
| **Public**           | ✅ Yes            | Only approved (they only see approved docs) |

**Note:** Status badge visibility follows document visibility rules. If you can see the document, you can see its status.

---

## 📋 Approvals Page - Rejected Tab

### Now Shows:

- ✅ Documents with `approval_status = "rejected"`
- ✅ Documents with `approval_status = "changes_requested"`
- ✅ Rejection reason (when clicked to view details)
- ✅ Uploader information
- ✅ Institution information
- ✅ Submission date

### Actions Available:

- 👁️ **View** - Opens document detail page
- (No approve/reject buttons on rejected tab - already processed)

---

## 🧪 Testing Checklist

### Backend Testing:

- [x] Admins can fetch rejected documents
- [x] Document list includes approval_status field
- [x] Rejected documents appear in API response
- [x] Archived and flagged documents also visible

### Frontend Testing:

- [x] Status badge appears in document explorer
- [x] Badge colors match status correctly
- [x] Badge text is readable
- [x] Works in dark mode
- [x] Rejected tab shows rejected documents
- [x] Badge appears on all document cards

### Integration Testing:

- [x] Reject a document → appears in Rejected tab
- [x] Rejected document shows red badge in explorer
- [x] Approved document shows green badge
- [x] Pending document shows yellow badge
- [x] Draft document shows gray badge

---

## 🎨 Status Badge Design

### Color Scheme:

```
APPROVED        → Green  (success, good to go)
PENDING         → Yellow (waiting, needs attention)
REJECTED        → Red    (error, needs fixing)
DRAFT           → Gray   (neutral, not submitted)
UNDER_REVIEW    → Blue   (in progress)
CHANGES_REQ     → Blue   (needs revision)
ARCHIVED        → Blue   (informational)
FLAGGED         → Blue   (warning)
```

### Typography:

- Font size: `text-xs` (12px)
- Font weight: `font-medium`
- Text transform: UPPERCASE
- Padding: `px-2 py-1`
- Border radius: `rounded-full` (pill shape)

---

## ✅ Summary

**Changes Made:**

1. ✅ Backend now includes rejected documents for admins
2. ✅ Backend returns approval_status in document list
3. ✅ Frontend displays status badge in document explorer
4. ✅ Rejected tab now shows rejected documents
5. ✅ Color-coded badges for quick status recognition

**Result:**

- ✅ Admins can see and manage rejected documents
- ✅ All users can see document approval status at a glance
- ✅ Better user experience with visual status indicators
- ✅ Consistent design across Approvals and Explorer pages

**User Experience:**

- ✅ No need to click to see document status
- ✅ Quick visual scanning of document states
- ✅ Professional appearance
- ✅ Accessible color scheme
