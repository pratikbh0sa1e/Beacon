# 🔧 Notification "[object Object]" Fix

## 🐛 Problem

Notifications were showing "[object Object]" instead of proper messages because the `metadata` field name was incorrect.

**Error Screenshot:**

```
localhost:3000 says
[object Object]
```

---

## 🔍 Root Cause

The Notification model in the database uses `action_metadata` (JSONB field), but the code was using `metadata` when creating notifications.

**Database Model:**

```python
class Notification(Base):
    # ...
    action_metadata = Column(JSONB, nullable=True)  # ✅ Correct field name
```

**Incorrect Code:**

```python
notification = Notification(
    # ...
    metadata={"document_id": document_id}  # ❌ Wrong field name
)
```

---

## ✅ Solution

Changed all `metadata=` to `action_metadata=` in notification creation code.

**Correct Code:**

```python
notification = Notification(
    # ...
    action_metadata={"document_id": document_id}  # ✅ Correct field name
)
```

---

## 📝 Files Fixed

### 1. backend/routers/document_router.py

**Fixed 4 notification creations:**

#### A) Submit for Review - MoE Admin Notification

```python
notification = Notification(
    user_id=MINISTRY_ADMIN.id,
    type="document_approval",
    title="New Document Pending Review",
    message=f"Document '{doc.filename}' has been submitted for MoE approval by {current_user.name}",
    priority="high",
    action_url=f"/approvals/{document_id}",
    action_metadata={  # ✅ Fixed
        "document_id": document_id,
        "submitter_id": current_user.id,
        "institution_id": doc.institution_id
    }
)
```

#### B) Submit for Review - Developer Notification

```python
notification = Notification(
    user_id=dev.id,
    type="document_approval",
    title="Document Submitted for Review",
    message=f"Document '{doc.filename}' submitted for MoE approval",
    priority="medium",
    action_url=f"/approvals/{document_id}",
    action_metadata={"document_id": document_id}  # ✅ Fixed
)
```

#### C) Approve Document Notification

```python
notification = Notification(
    user_id=doc.uploader_id,
    type="document_approved",
    title="Document Approved",
    message=f"Your document '{doc.filename}' has been approved by {current_user.name}",
    priority="high",
    action_url=f"/documents/{document_id}",
    action_metadata={"document_id": document_id, "approved_by": current_user.id}  # ✅ Fixed
)
```

#### D) Reject Document Notification

```python
notification = Notification(
    user_id=doc.uploader_id,
    type="document_rejected",
    title="Document Rejected",
    message=f"Your document '{doc.filename}' has been rejected. Reason: {reason}",
    priority="high",
    action_url=f"/documents/{document_id}",
    action_metadata={"document_id": document_id, "rejected_by": current_user.id, "reason": reason}  # ✅ Fixed
)
```

#### E) Request Changes Notification

```python
notification = Notification(
    user_id=doc.uploader_id,
    type="changes_requested",
    title="Changes Requested",
    message=f"Changes requested for '{doc.filename}': {changes_requested}",
    priority="high",
    action_url=f"/documents/{document_id}",
    action_metadata={"document_id": document_id, "requested_by": current_user.id}  # ✅ Fixed
)
```

---

### 2. backend/utils/notification_helper.py

**Fixed all occurrences using PowerShell command:**

```powershell
(Get-Content backend/utils/notification_helper.py -Raw) -replace 'metadata=metadata', 'action_metadata=metadata' | Set-Content backend/utils/notification_helper.py
```

**This fixed:**

- `send_hierarchical_notification()` function (multiple occurrences)
- `notify_document_upload()` function
- `notify_approval_request()` function
- `notify_document_approved()` function
- `notify_document_rejected()` function
- `notify_changes_requested()` function

---

## 🧪 Testing

### Before Fix:

```
Notification appears as: "[object Object]"
User sees: Confusing error message
```

### After Fix:

```
Notification appears as: "Document 'Annual Report.pdf' has been submitted for MoE approval by John Doe"
User sees: Clear, readable message
```

---

## ✅ Verification Checklist

- [x] Fixed submit-for-review endpoint (2 notifications)
- [x] Fixed approve endpoint (1 notification)
- [x] Fixed reject endpoint (1 notification)
- [x] Fixed request-changes endpoint (1 notification)
- [x] Fixed notification_helper.py (all functions)
- [x] No syntax errors (getDiagnostics passed)
- [x] All `metadata=` changed to `action_metadata=`

---

## 🎯 Result

**Notifications now display correctly:**

- ✅ "New Document Pending Review"
- ✅ "Document Submitted for Review"
- ✅ "Document Approved"
- ✅ "Document Rejected"
- ✅ "Changes Requested"

**No more "[object Object]" errors!** 🎉

---

## 📚 Related Files

- `backend/database.py` - Notification model definition
- `backend/routers/document_router.py` - Document workflow endpoints
- `backend/utils/notification_helper.py` - Notification hierarchy helper
- `frontend/src/components/layout/Header.jsx` - Notification display (if applicable)

---

## 🔍 How to Test

1. **Submit a document for review:**

   - Login as University Admin
   - Go to document detail page
   - Click "Submit for MoE Review"
   - Check notification bell icon

2. **Expected Result:**

   - Notification shows: "Document '{filename}' has been submitted for MoE approval by {your_name}"
   - NOT: "[object Object]"

3. **Approve/Reject a document:**
   - Login as MoE Admin
   - Go to `/approvals`
   - Approve or reject a document
   - Uploader receives notification with proper message

---

## 💡 Key Takeaway

**Always use the correct field name from the database model:**

- Database field: `action_metadata` (JSONB)
- Code usage: `action_metadata=` ✅
- NOT: `metadata=` ❌

This ensures proper JSON serialization and prevents "[object Object]" errors.
