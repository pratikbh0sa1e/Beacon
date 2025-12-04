# Changes Requested Documents - Visibility Rules

## Current Behavior (NEEDS FIX)

### Who Can See "Changes Requested" Documents:

- ✅ Developer (all)
- ✅ Ministry Admin (all - **WRONG!**)
- ✅ University Admin (all - **WRONG!**)
- ✅ Document Officer (only their own)
- ❌ Students (none)
- ❌ Public (none)

**Problem:** Ministry admins and university admins can see ALL changes_requested documents, not just from their institutions!

---

## Correct Behavior (SHOULD BE)

### Who SHOULD See "Changes Requested" Documents:

| Role                 | Can See                                        |
| -------------------- | ---------------------------------------------- |
| **Developer**        | ✅ All changes_requested documents             |
| **Ministry Admin**   | ✅ Only from institutions under their ministry |
| **University Admin** | ✅ Only from their own institution             |
| **Document Officer** | ✅ Only documents they uploaded                |
| **Uploader**         | ✅ Only documents they uploaded                |
| **Student**          | ❌ None                                        |
| **Public**           | ❌ None                                        |

---

## Where Changes Requested Documents Appear

### 1. Document Explorer Page

**Current:** Shows to all admins
**Should:** Filter by institution hierarchy

### 2. Approvals Page - "Rejected/Changes" Tab

**Current:** Shows all rejected/changes_requested
**Should:** Filter by institution hierarchy

### 3. Document Detail Page

**Current:** Shows rejection reason to anyone who can access
**Should:** Only show to uploader, their institution admins, and developer

---

## Use Case Examples

### Example 1: IIT Delhi Document

**Document:**

- Uploaded by: IIT Delhi Document Officer
- Institution: IIT Delhi (under Ministry of Education)
- Status: changes_requested
- Reason: "Please update the date format"

**Who Should See:**

- ✅ Developer
- ✅ Ministry of Education Admin (parent ministry)
- ✅ IIT Delhi University Admin (same institution)
- ✅ The uploader (Document Officer)
- ❌ Ministry of Health Admin (different ministry)
- ❌ IIT Mumbai Admin (different institution)
- ❌ Students
- ❌ Public

---

### Example 2: AIIMS Document

**Document:**

- Uploaded by: AIIMS Document Officer
- Institution: AIIMS Delhi (under Ministry of Health)
- Status: changes_requested
- Reason: "Missing signatures"

**Who Should See:**

- ✅ Developer
- ✅ Ministry of Health Admin (parent ministry)
- ✅ AIIMS University Admin (same institution)
- ✅ The uploader (Document Officer)
- ❌ Ministry of Education Admin (different ministry)
- ❌ IIT Delhi Admin (different institution)
- ❌ Students
- ❌ Public

---

## Current Code Issues

### Issue 1: Document List Endpoint

**Location:** `backend/routers/document_router.py` - `list_documents()`

**Current Code:**

```python
elif current_user.role in ["ministry_admin", "university_admin"]:
    # Admins see: approved, pending, under_review, changes_requested, rejected
    query = query.filter(
        or_(
            Document.approval_status.in_(["approved", "pending", "under_review", "changes_requested", "rejected"]),
            Document.uploader_id == current_user.id
        )
    )
```

**Problem:** Shows ALL changes_requested documents to ALL admins!

**Should Be:**

```python
elif current_user.role == "ministry_admin":
    # Ministry admin sees documents from institutions under their ministry
    child_institution_ids = get_child_institutions(current_user.institution_id)
    query = query.filter(
        or_(
            # Approved public documents
            and_(Document.approval_status == "approved", Document.visibility_level == "public"),
            # Pending documents from their institutions
            and_(
                Document.approval_status.in_(["pending", "under_review"]),
                Document.institution_id.in_(child_institution_ids)
            ),
            # Changes requested/rejected from their institutions
            and_(
                Document.approval_status.in_(["changes_requested", "rejected"]),
                Document.institution_id.in_(child_institution_ids)
            ),
            # Their own uploads
            Document.uploader_id == current_user.id
        )
    )

elif current_user.role == "university_admin":
    # University admin sees documents from their institution only
    query = query.filter(
        or_(
            # Approved public documents
            and_(Document.approval_status == "approved", Document.visibility_level == "public"),
            # Any status from their institution
            Document.institution_id == current_user.institution_id,
            # Their own uploads
            Document.uploader_id == current_user.id
        )
    )
```

---

### Issue 2: Approvals Page Endpoint

**Location:** `backend/routers/document_router.py` - `get_pending_approvals()`

**Current:** Already fixed! ✅ Filters by institution hierarchy

---

## Recommended Fix

### Step 1: Update Document List Filtering

Split the admin filtering into separate logic for ministry_admin and university_admin:

```python
# Ministry Admin: Only see documents from institutions under their ministry
elif current_user.role == "ministry_admin":
    # Get child institutions
    child_institution_ids = db.query(Institution.id).filter(
        Institution.parent_ministry_id == current_user.institution_id,
        Institution.deleted_at == None
    ).all()
    child_institution_ids = [inst_id[0] for inst_id in child_institution_ids]

    query = query.filter(
        or_(
            # Public approved documents (everyone sees)
            and_(
                Document.approval_status == "approved",
                Document.visibility_level == "public"
            ),
            # Documents from their institutions (any status)
            and_(
                Document.institution_id.in_(child_institution_ids),
                Document.approval_status.in_(["pending", "under_review", "changes_requested", "rejected", "approved"])
            ),
            # Their own uploads
            Document.uploader_id == current_user.id
        )
    )

# University Admin: Only see documents from their institution
elif current_user.role == "university_admin":
    query = query.filter(
        or_(
            # Public approved documents
            and_(
                Document.approval_status == "approved",
                Document.visibility_level == "public"
            ),
            # Documents from their institution (any status)
            Document.institution_id == current_user.institution_id,
            # Their own uploads
            Document.uploader_id == current_user.id
        )
    )
```

---

## Privacy & Security Benefits

### Before Fix:

- ❌ Ministry of Education admin can see AIIMS rejected documents
- ❌ IIT Delhi admin can see IIT Mumbai rejected documents
- ❌ Privacy leak across institutions

### After Fix:

- ✅ Ministry admins only see documents from their institutions
- ✅ University admins only see documents from their institution
- ✅ Clear institutional boundaries
- ✅ No cross-ministry data leakage

---

## Summary

**Current Issue:**

- Changes requested documents visible to ALL admins
- No institutional filtering
- Privacy concerns

**Fix Needed:**

- Filter by institution hierarchy
- Ministry admin → only their institutions
- University admin → only their institution
- Uploader → only their documents

**Impact:**

- Better privacy
- Clear boundaries
- Follows institutional hierarchy
- Prevents data leakage

---

**Status:** ⚠️ NEEDS FIX

**Priority:** HIGH (Privacy/Security Issue)

**Files to Update:**

- `backend/routers/document_router.py` - `list_documents()` function
