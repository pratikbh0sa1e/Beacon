# 📝 Draft and Approval Workflow Explained

## 🔄 Document Lifecycle

```
Upload → Draft → Submit for Review → Pending → Approved/Rejected
```

---

## 1️⃣ DRAFT STATUS

### What is Draft?

- **Initial state** when a document is uploaded
- Document is **NOT visible** to the public
- Document is **NOT searchable** by regular users
- Only visible to:
  - ✅ The uploader (owner)
  - ✅ University Admin (from same institution)
  - ✅ Developer (god mode)

### When Does a Document Become Draft?

```python
# When uploaded, approval_status is set to "draft"
approval_status = "draft"
requires_moe_approval = False
```

### Who Can See Draft Documents?

| Role                 | Can See Own Drafts | Can See Others' Drafts |
| -------------------- | ------------------ | ---------------------- |
| **Developer**        | ✅                 | ✅ (All drafts)        |
| **MoE Admin**        | ✅                 | ❌                     |
| **University Admin** | ✅                 | ✅ (Same institution)  |
| **Document Officer** | ✅                 | ❌                     |
| **Student**          | ❌                 | ❌                     |
| **Public**           | ❌                 | ❌                     |

### Draft Document Behavior

- **In Document Explorer:** Only uploader and admins see it
- **In Search Results:** Does NOT appear for regular users
- **Direct Access:** Only uploader and admins can access
- **Download:** Follows normal download permissions

---

## 2️⃣ SUBMIT FOR REVIEW

### How to Submit?

1. Uploader or University Admin goes to document detail page
2. Clicks **"Submit for MoE Review"** button
3. Confirms submission

### What Happens?

```python
approval_status = "pending"
requires_moe_approval = True
escalated_at = datetime.utcnow()
```

### Notifications Sent:

- **MoE Admin** receives notification (primary)
- **Developer** receives copy notification

### Who Can Submit?

- ✅ Document uploader
- ✅ University Admin (same institution)
- ✅ Developer

---

## 3️⃣ PENDING STATUS

### What is Pending?

- Document is **waiting for MoE approval**
- Document is **visible to MoE Admin** in approval dashboard
- Document is **still not public** (unless visibility is public AND approved)

### Who Can See Pending Documents?

| Role                 | Can See                                   |
| -------------------- | ----------------------------------------- |
| **Developer**        | ✅ All pending                            |
| **MoE Admin**        | ✅ Only if `requires_moe_approval = True` |
| **University Admin** | ✅ From their institution                 |
| **Document Officer** | ❌                                        |
| **Student**          | ❌                                        |
| **Public**           | ❌                                        |

### Pending Document Behavior

- **In Approval Dashboard:** Visible to MoE Admin and University Admin
- **In Document Explorer:** NOT visible to regular users
- **Direct Access:** Only admins can access

---

## 4️⃣ APPROVAL ACTIONS

### MoE Admin Can:

#### A) Approve ✅

```python
approval_status = "approved"
approved_by = current_user.id
approved_at = datetime.utcnow()
```

- Document becomes **publicly visible** (based on visibility level)
- Uploader receives notification
- Document appears in search results

#### B) Reject ❌

```python
approval_status = "rejected"
rejection_reason = "Reason provided by admin"
```

- Document stays **hidden** from public
- Uploader receives notification with reason
- Uploader can edit and resubmit

#### C) Request Changes ⚠️

```python
approval_status = "changes_requested"
rejection_reason = "Changes needed: ..."
```

- Document stays **hidden** from public
- Uploader receives notification with requested changes
- Uploader can edit and resubmit

---

## 5️⃣ APPROVED STATUS

### What is Approved?

- Document has been **reviewed and approved**
- Document is **publicly visible** (based on visibility level)
- Document appears in **search results**
- Document is **downloadable** (if download_allowed = True)

### Who Can See Approved Documents?

Depends on **visibility level**:

| Visibility           | Who Can See                              |
| -------------------- | ---------------------------------------- |
| **Public**           | Everyone                                 |
| **Institution-Only** | Same institution members                 |
| **Restricted**       | Admins + Doc Officers (same institution) |
| **Confidential**     | Admins only (same institution)           |

---

## 6️⃣ OTHER STATUSES

### Under Review

```python
approval_status = "under_review"
```

- MoE Admin is actively reviewing
- Same visibility as "pending"

### Changes Requested

```python
approval_status = "changes_requested"
```

- Uploader needs to make changes
- Only visible to uploader and admins

### Rejected

```python
approval_status = "rejected"
```

- Document was rejected
- Only visible to uploader and admins
- Can be edited and resubmitted

### Archived

```python
approval_status = "archived"
```

- Document is no longer active
- Only visible in archive filters

### Flagged

```python
approval_status = "flagged"
```

- Document is under dispute
- Visible to admins only

### Expired

```python
approval_status = "expired"
```

- Document validity has ended
- Requires renewal or archival

---

## 🔐 VISIBILITY MATRIX

### Draft Documents

| User Role   | Own Drafts | Others' Drafts (Same Inst) | Others' Drafts (Diff Inst) |
| ----------- | ---------- | -------------------------- | -------------------------- |
| Developer   | ✅         | ✅                         | ✅                         |
| MoE Admin   | ✅         | ❌                         | ❌                         |
| Uni Admin   | ✅         | ✅                         | ❌                         |
| Doc Officer | ✅         | ❌                         | ❌                         |
| Student     | ❌         | ❌                         | ❌                         |

### Pending Documents

| User Role   | Can See in Approval Dashboard                      |
| ----------- | -------------------------------------------------- |
| Developer   | ✅ All pending                                     |
| MoE Admin   | ✅ Only escalated (`requires_moe_approval = True`) |
| Uni Admin   | ✅ From their institution                          |
| Doc Officer | ❌                                                 |
| Student     | ❌                                                 |

### Approved Documents

Follows normal **visibility level** rules (public, institution-only, restricted, confidential)

---

## 📊 WORKFLOW EXAMPLES

### Example 1: University Internal Document (No MoE Review)

```
1. Doc Officer uploads → Status: draft
2. Only visible to: Uploader, Uni Admin, Developer
3. Uni Admin approves internally (optional future feature)
4. Status changes to: approved
5. Visible to: Institution members (if institution-only)
```

### Example 2: Document Requiring MoE Approval

```
1. Doc Officer uploads → Status: draft
2. Uni Admin clicks "Submit for MoE Review"
3. Status: pending, requires_moe_approval: True
4. MoE Admin sees in approval dashboard
5. MoE Admin approves → Status: approved
6. Document becomes public (based on visibility)
```

### Example 3: Document Rejected

```
1. Doc Officer uploads → Status: draft
2. Uni Admin submits for review → Status: pending
3. MoE Admin rejects with reason → Status: rejected
4. Doc Officer receives notification
5. Doc Officer edits document
6. Uni Admin resubmits → Status: pending (again)
7. MoE Admin approves → Status: approved
```

---

## 🎯 KEY PRINCIPLES

### 1. Privacy by Default

- New documents start as **draft**
- Not visible to public until approved
- Protects incomplete/sensitive documents

### 2. Institutional Autonomy

- Universities control their documents
- MoE only sees what's **explicitly submitted**
- Draft documents stay private

### 3. Explicit Escalation

- MoE approval is **opt-in**, not automatic
- University decides when to escalate
- "Submit for MoE Review" button is the trigger

### 4. Role-Based Access

- Each role sees appropriate documents
- Admins see more than regular users
- Uploader always sees their own documents

### 5. Audit Trail

- All status changes are tracked
- Approval/rejection reasons stored
- Timestamps recorded

---

## 🔧 TECHNICAL IMPLEMENTATION

### Database Fields

```python
class Document:
    approval_status = Column(String(50), default="draft")
    # Values: draft, pending, under_review, changes_requested,
    #         approved, restricted_approved, archived, rejected,
    #         flagged, expired

    requires_moe_approval = Column(Boolean, default=False)
    # True when submitted for MoE review

    escalated_at = Column(DateTime, nullable=True)
    # Timestamp when submitted for review

    approved_by = Column(Integer, ForeignKey("users.id"))
    # Who approved/rejected

    approved_at = Column(DateTime, nullable=True)
    # When approved/rejected

    rejection_reason = Column(Text, nullable=True)
    # Reason for rejection or changes requested
```

### API Endpoints

```python
# Submit for review
POST /documents/{id}/submit-for-review

# Approve
POST /documents/{id}/approve

# Reject
POST /documents/{id}/reject
Body: { "reason": "..." }

# Request changes
POST /documents/{id}/request-changes
Body: { "changes_requested": "..." }

# Get pending approvals
GET /documents/approvals/pending
```

---

## ✅ SUMMARY

**Draft Status:**

- Initial state after upload
- Private to uploader and admins
- Not searchable by public

**Submit for Review:**

- Explicit action by University Admin
- Sets `requires_moe_approval = True`
- Triggers notification to MoE

**Pending Status:**

- Waiting for MoE approval
- Visible in approval dashboard
- Still not public

**Approved Status:**

- Reviewed and approved
- Publicly visible (based on visibility level)
- Searchable and accessible

**Key Point:** MoE Admin **ONLY** sees documents when University explicitly submits them for review. This maintains institutional autonomy while enabling proper oversight.
