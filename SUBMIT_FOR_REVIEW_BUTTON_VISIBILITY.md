# 🔘 "Submit for MoE Review" Button - Visibility Rules

## 🎯 Who Can See the Button?

The "Submit for MoE Review" button appears on the document detail page based on **3 conditions**:

### Condition 1: User Role ✅

**Button visible to:**

- ✅ **Developer** (god mode - can submit any document)
- ✅ **University Admin** (can submit documents from their institution)
- ✅ **Document Uploader** (can submit their own documents)

**Button NOT visible to:**

- ❌ **MoE Admin** (they receive submissions, don't submit)
- ❌ **Document Officer** (unless they are the uploader)
- ❌ **Student** (unless they are the uploader)
- ❌ **Public Viewer** (no access)

### Condition 2: Document Status ✅

**Button visible when document status is:**

- ✅ `draft` - Not yet submitted
- ✅ `rejected` - Was rejected, can resubmit
- ✅ `changes_requested` - Changes requested, can resubmit
- ✅ `archived` - Can reactivate and submit
- ✅ `flagged` - Can resolve and submit
- ✅ `expired` - Can renew and submit

**Button NOT visible when:**

- ❌ `pending` - Already submitted, waiting for review
- ❌ `approved` - Already approved, no need to submit
- ❌ `under_review` - Currently being reviewed
- ❌ `restricted_approved` - Already approved with restrictions

### Condition 3: Institution Match ✅

**For University Admin:**

- ✅ Can submit documents from **their own institution**
- ❌ Cannot submit documents from **other institutions**

**For Developer:**

- ✅ Can submit documents from **any institution**

**For Uploader:**

- ✅ Can submit **their own documents** (regardless of institution)

---

## 📋 COMPLETE VISIBILITY MATRIX

### By Role and Document Status

| User Role                      | Draft | Pending | Approved | Rejected | Changes Requested | Under Review |
| ------------------------------ | ----- | ------- | -------- | -------- | ----------------- | ------------ |
| **Developer**                  | ✅    | ❌      | ❌       | ✅       | ✅                | ❌           |
| **MoE Admin**                  | ❌    | ❌      | ❌       | ❌       | ❌                | ❌           |
| **Uni Admin (Same Inst)**      | ✅    | ❌      | ❌       | ✅       | ✅                | ❌           |
| **Uni Admin (Diff Inst)**      | ❌    | ❌      | ❌       | ❌       | ❌                | ❌           |
| **Doc Officer (Uploader)**     | ✅    | ❌      | ❌       | ✅       | ✅                | ❌           |
| **Doc Officer (Not Uploader)** | ❌    | ❌      | ❌       | ❌       | ❌                | ❌           |
| **Student (Uploader)**         | ✅    | ❌      | ❌       | ✅       | ✅                | ❌           |
| **Student (Not Uploader)**     | ❌    | ❌      | ❌       | ❌       | ❌                | ❌           |

---

## 🔐 PERMISSION LOGIC

### Frontend Logic (DocumentDetailPage.jsx)

```javascript
// Button shows if:
(user?.role === "university_admin" || user?.role === "developer") &&
  docData.approval_status !== "pending" &&
  docData.approval_status !== "approved";
```

**Current Implementation:**

- ✅ Checks user role (university_admin or developer)
- ✅ Checks document is not pending
- ✅ Checks document is not approved
- ⚠️ **Missing:** Uploader check (should allow uploader to submit)
- ⚠️ **Missing:** Institution match check (frontend only)

### Backend Logic (document_router.py)

```python
# Permission check:
if current_user.role not in ["university_admin", "developer"] and current_user.id != doc.uploader_id:
    raise HTTPException(status_code=403, detail="Only University Admin can submit documents for review")

# Institution check:
if current_user.role == "university_admin" and current_user.institution_id != doc.institution_id:
    raise HTTPException(status_code=403, detail="Can only submit documents from your institution")
```

**Backend Implementation:**

- ✅ Checks user role (university_admin, developer, or uploader)
- ✅ Checks institution match for university admin
- ✅ Allows uploader to submit their own documents
- ✅ Proper error messages

---

## 🎯 REAL-WORLD SCENARIOS

### Scenario 1: University Admin Views Their Institution's Document

```
User: University A Admin
Document: Uploaded by Doc Officer from University A
Status: draft

Button Visible: ✅ YES
Reason: University Admin can submit documents from their institution
```

### Scenario 2: University Admin Views Another Institution's Document

```
User: University A Admin
Document: Uploaded by University B Admin
Status: draft

Button Visible: ❌ NO
Reason: Cannot submit documents from other institutions
```

### Scenario 3: Document Officer Views Their Own Document

```
User: Document Officer from University A
Document: Uploaded by themselves
Status: draft

Button Visible: ✅ YES (Backend allows, but frontend needs update)
Reason: Uploader can submit their own documents
```

### Scenario 4: Document Officer Views Someone Else's Document

```
User: Document Officer from University A
Document: Uploaded by another Doc Officer
Status: draft

Button Visible: ❌ NO
Reason: Not the uploader, not an admin
```

### Scenario 5: MoE Admin Views Any Document

```
User: MoE Admin
Document: Any document
Status: draft

Button Visible: ❌ NO
Reason: MoE Admin receives submissions, doesn't submit
```

### Scenario 6: Developer Views Any Document

```
User: Developer
Document: Any document from any institution
Status: draft

Button Visible: ✅ YES
Reason: Developer has god mode access
```

### Scenario 7: Document Already Pending

```
User: University Admin
Document: From their institution
Status: pending

Button Visible: ❌ NO
Reason: Already submitted, waiting for review
```

### Scenario 8: Document Already Approved

```
User: University Admin
Document: From their institution
Status: approved

Button Visible: ❌ NO
Reason: Already approved, no need to submit again
```

### Scenario 9: Document Rejected - Can Resubmit

```
User: University Admin
Document: From their institution
Status: rejected

Button Visible: ✅ YES
Reason: Can resubmit after addressing rejection reasons
```

---

## 🔧 RECOMMENDED FRONTEND UPDATE

The current frontend logic should be updated to match backend permissions:

### Current Code:

```javascript
{
  (user?.role === "university_admin" || user?.role === "developer") &&
    docData.approval_status !== "pending" &&
    docData.approval_status !== "approved" && (
      <Button onClick={handleSubmitForReview}>Submit for MoE Review</Button>
    );
}
```

### Recommended Code:

```javascript
{
  /* Show button if:
    1. User is Developer (god mode), OR
    2. User is University Admin from same institution, OR
    3. User is the uploader
    AND document is not pending/approved
*/
}
{
  (user?.role === "developer" ||
    (user?.role === "university_admin" &&
      user?.institution_id === docData.institution_id) ||
    user?.id === docData.uploader_id) &&
    docData.approval_status !== "pending" &&
    docData.approval_status !== "approved" &&
    docData.approval_status !== "under_review" && (
      <Button onClick={handleSubmitForReview}>Submit for MoE Review</Button>
    );
}
```

This would:

- ✅ Allow uploaders to submit their own documents
- ✅ Check institution match for university admin
- ✅ Hide button when under review
- ✅ Match backend permission logic exactly

---

## 📊 SUMMARY TABLE

### Who Can Click "Submit for MoE Review"?

| User Type            | Can Submit Own Docs | Can Submit Others' Docs (Same Inst) | Can Submit Others' Docs (Diff Inst) |
| -------------------- | ------------------- | ----------------------------------- | ----------------------------------- |
| **Developer**        | ✅                  | ✅                                  | ✅                                  |
| **MoE Admin**        | ✅\*                | ❌                                  | ❌                                  |
| **University Admin** | ✅                  | ✅                                  | ❌                                  |
| **Document Officer** | ✅                  | ❌                                  | ❌                                  |
| **Student**          | ✅                  | ❌                                  | ❌                                  |
| **Public**           | ❌                  | ❌                                  | ❌                                  |

\*MoE Admin can submit their own documents, but button is currently hidden in frontend

---

## 🎯 KEY PRINCIPLES

### 1. Institutional Control

- University Admin controls what gets submitted from their institution
- Cannot submit documents from other institutions
- Maintains institutional autonomy

### 2. Uploader Rights

- Uploaders can submit their own documents
- Even if they're not admins
- Ownership principle

### 3. Developer Override

- Developer can submit any document
- God mode for system management
- No restrictions

### 4. MoE Admin Exclusion

- MoE Admin does NOT submit documents
- They RECEIVE submissions
- They APPROVE/REJECT submissions
- Maintains separation of roles

### 5. Status-Based Visibility

- Cannot submit if already pending
- Cannot submit if already approved
- Can resubmit if rejected
- Can resubmit if changes requested

---

## ✅ CURRENT IMPLEMENTATION STATUS

**Frontend:**

- ✅ Shows button for Developer
- ✅ Shows button for University Admin
- ✅ Hides button when pending
- ✅ Hides button when approved
- ⚠️ Missing: Uploader check
- ⚠️ Missing: Institution match check
- ⚠️ Missing: Under review check

**Backend:**

- ✅ Allows Developer
- ✅ Allows University Admin (same institution)
- ✅ Allows Uploader
- ✅ Checks institution match
- ✅ Proper error messages
- ✅ Sets escalation flag
- ✅ Sends notifications

**Recommendation:** Update frontend to match backend logic for consistency.
