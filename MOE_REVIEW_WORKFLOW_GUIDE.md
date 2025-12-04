# 📋 MoE Review Workflow - Complete Guide

## 🎯 Where Does MoE Admin Review Documents?

MoE Admin reviews documents in the **Document Approvals Page** at `/approvals`

---

## 🔄 COMPLETE WORKFLOW

### Step 1: University Uploads Document

```
Location: /upload
User: Document Officer or University Admin
Action: Upload document
Result: Document created with status = "draft"
```

**What Happens:**

- Document is saved to database
- `approval_status = "draft"`
- `requires_moe_approval = False`
- Only visible to uploader and university admin

---

### Step 2: University Submits for MoE Review

```
Location: /documents/{id} (Document Detail Page)
User: University Admin or Uploader
Action: Click "Submit for MoE Review" button
Result: Document escalated to MoE
```

**What Happens:**

```python
# Backend changes:
approval_status = "pending"
requires_moe_approval = True
escalated_at = datetime.utcnow()

# Notifications sent:
- MoE Admin receives notification (high priority)
- Developer receives copy notification (medium priority)
```

**Button Visibility:**

- ✅ Shows for: Developer, University Admin (same inst), Uploader
- ✅ Shows when status: draft, rejected, changes_requested, archived, flagged, expired
- ❌ Hidden when status: pending, approved, under_review

---

### Step 3: MoE Admin Receives Notification

```
Location: Notification bell icon (top right)
User: MoE Admin
Action: Click notification
Result: Redirected to /approvals/{document_id}
```

**Notification Content:**

```
Title: "New Document Pending Review"
Message: "Document '{filename}' has been submitted for MoE approval by {uploader_name}"
Priority: High
Action: Click to view in approvals
```

---

### Step 4: MoE Admin Reviews Document

```
Location: /approvals (Document Approvals Page)
User: MoE Admin
Action: View list of pending documents
Result: See all documents requiring MoE approval
```

**What MoE Admin Sees:**

#### Approvals Dashboard (`/approvals`)

```
┌─────────────────────────────────────────────────────┐
│  Document Approvals                                  │
├─────────────────────────────────────────────────────┤
│  Stats:                                              │
│  • Pending: 5 documents                              │
│  • Your Role: MoE Admin                              │
│  • Institution: Ministry of Education                │
├─────────────────────────────────────────────────────┤
│  Document Card 1:                                    │
│  ┌───────────────────────────────────────────────┐  │
│  │ Title: University A Annual Report             │  │
│  │ Category: Report                               │  │
│  │ Institution: University A                      │  │
│  │ Uploader: John Doe (University Admin)         │  │
│  │ Submitted: 2024-12-02 10:30 AM                │  │
│  │ Visibility: Public                             │  │
│  │                                                │  │
│  │ [✅ Approve] [⚠️ Request Changes] [❌ Reject]  │  │
│  │ [View Details]                                 │  │
│  └───────────────────────────────────────────────┘  │
│                                                      │
│  Document Card 2: ...                                │
└─────────────────────────────────────────────────────┘
```

**Filtering:**

- MoE Admin ONLY sees documents where `requires_moe_approval = True`
- Documents are sorted by submission date (most recent first)
- Shows institution name, uploader, and submission time

---

### Step 5: MoE Admin Takes Action

#### Option A: Approve ✅

```
Location: /approvals
User: MoE Admin
Action: Click "Approve" button
Result: Document approved
```

**What Happens:**

```python
# Backend changes:
approval_status = "approved"
approved_by = MINISTRY_ADMIN.id
approved_at = datetime.utcnow()

# Notifications sent:
- Uploader receives "Document Approved" notification
- Document becomes publicly visible (based on visibility level)
```

**Modal Dialog:**

```
┌─────────────────────────────────────┐
│ Approve Document                     │
├─────────────────────────────────────┤
│ Document: University A Annual Report │
│                                      │
│ Are you sure you want to approve    │
│ this document? It will become        │
│ visible according to its visibility  │
│ settings.                            │
│                                      │
│ [Confirm] [Cancel]                   │
└─────────────────────────────────────┘
```

---

#### Option B: Request Changes ⚠️

```
Location: /approvals
User: MoE Admin
Action: Click "Request Changes" button
Result: Document sent back for revisions
```

**What Happens:**

```python
# Backend changes:
approval_status = "changes_requested"
rejection_reason = "Changes needed: [MoE Admin's feedback]"

# Notifications sent:
- Uploader receives "Changes Requested" notification with details
```

**Modal Dialog:**

```
┌─────────────────────────────────────┐
│ Request Changes                      │
├─────────────────────────────────────┤
│ Document: University A Annual Report │
│                                      │
│ Changes needed:                      │
│ ┌─────────────────────────────────┐ │
│ │ [Text area for feedback]        │ │
│ │                                 │ │
│ │                                 │ │
│ └─────────────────────────────────┘ │
│                                      │
│ [Confirm] [Cancel]                   │
└─────────────────────────────────────┘
```

---

#### Option C: Reject ❌

```
Location: /approvals
User: MoE Admin
Action: Click "Reject" button
Result: Document rejected
```

**What Happens:**

```python
# Backend changes:
approval_status = "rejected"
rejection_reason = "Reason: [MoE Admin's reason]"
approved_by = MINISTRY_ADMIN.id
approved_at = datetime.utcnow()

# Notifications sent:
- Uploader receives "Document Rejected" notification with reason
```

**Modal Dialog:**

```
┌─────────────────────────────────────┐
│ Reject Document                      │
├─────────────────────────────────────┤
│ Document: University A Annual Report │
│                                      │
│ Reason for rejection:                │
│ ┌─────────────────────────────────┐ │
│ │ [Text area for reason]          │ │
│ │                                 │ │
│ │                                 │ │
│ └─────────────────────────────────┘ │
│                                      │
│ [Confirm] [Cancel]                   │
└─────────────────────────────────────┘
```

---

### Step 6: University Receives Feedback

#### If Approved:

```
Location: Notification bell
User: Uploader (University Admin or Doc Officer)
Notification: "Document Approved"
Message: "Your document 'University A Annual Report' has been approved by [MoE Admin Name]"
```

**Document Status:**

- `approval_status = "approved"`
- Document becomes visible based on visibility level
- Appears in public search results (if visibility = public)

---

#### If Changes Requested:

```
Location: Notification bell + Document Detail Page
User: Uploader
Notification: "Changes Requested"
Message: "Changes requested for 'University A Annual Report': [feedback]"
```

**Document Detail Page Shows:**

```
┌─────────────────────────────────────────────────┐
│ ⚠️ Changes Requested                            │
├─────────────────────────────────────────────────┤
│ Changes requested for this document:            │
│ "Please update the financial section with      │
│  Q4 data and add executive summary."           │
│                                                 │
│ [Submit for MoE Review] (button available)     │
└─────────────────────────────────────────────────┘
```

**What University Can Do:**

1. Edit the document (if edit feature exists)
2. Upload a new version
3. Click "Submit for MoE Review" again to resubmit

---

#### If Rejected:

```
Location: Notification bell + Document Detail Page
User: Uploader
Notification: "Document Rejected"
Message: "Your document 'University A Annual Report' has been rejected. Reason: [reason]"
```

**Document Detail Page Shows:**

```
┌─────────────────────────────────────────────────┐
│ ❌ Document Rejected                            │
├─────────────────────────────────────────────────┤
│ This document was rejected:                     │
│ "Document does not meet MoE standards for      │
│  annual reporting. Please revise and resubmit."│
│                                                 │
│ [Submit for MoE Review] (button available)     │
└─────────────────────────────────────────────────┘
```

**What University Can Do:**

1. Address the rejection reasons
2. Upload a corrected version
3. Click "Submit for MoE Review" again to resubmit

---

## 📍 KEY PAGES AND ROUTES

### For MoE Admin:

1. **Approvals Dashboard** - `/approvals`

   - Main review page
   - Lists all pending documents
   - Action buttons: Approve, Request Changes, Reject

2. **Document Detail** - `/documents/{id}`

   - View full document details
   - See document content
   - Access from "View Details" button in approvals

3. **Notifications** - Bell icon (top right)
   - Receive alerts when documents submitted
   - Click to go to approvals page

### For University Admin/Uploader:

1. **Document Detail** - `/documents/{id}`

   - View document
   - See status badge (draft, pending, approved, rejected)
   - Click "Submit for MoE Review" button
   - See rejection/change request reasons

2. **Document Explorer** - `/documents`

   - Browse all documents
   - Filter by status
   - See which documents are pending

3. **Upload Page** - `/upload`
   - Upload new documents
   - Documents start as "draft"

---

## 🔐 ACCESS CONTROL

### Who Can Access `/approvals` Page?

| Role                 | Can Access | What They See                                 |
| -------------------- | ---------- | --------------------------------------------- |
| **Developer**        | ✅         | All pending documents                         |
| **MoE Admin**        | ✅         | Documents with `requires_moe_approval = True` |
| **University Admin** | ✅         | Pending documents from their institution      |
| **Document Officer** | ❌         | No access                                     |
| **Student**          | ❌         | No access                                     |
| **Public**           | ❌         | No access                                     |

**Route Protection:**

```javascript
<Route
  path="approvals"
  element={
    <ProtectedRoute
      allowedRoles={["developer", "ministry_admin", "university_admin"]}
    >
      <ApprovalsPage />
    </ProtectedRoute>
  }
/>
```

---

## 📊 STATUS FLOW DIAGRAM

```
┌─────────┐
│  DRAFT  │ ← Document uploaded
└────┬────┘
     │ Click "Submit for MoE Review"
     ↓
┌─────────┐
│ PENDING │ ← MoE Admin sees in /approvals
└────┬────┘
     │
     ├─→ Approve → ┌──────────┐
     │             │ APPROVED │ → Publicly visible
     │             └──────────┘
     │
     ├─→ Request Changes → ┌────────────────────┐
     │                     │ CHANGES_REQUESTED  │ → Can resubmit
     │                     └────────────────────┘
     │
     └─→ Reject → ┌──────────┐
                  │ REJECTED │ → Can resubmit
                  └──────────┘
```

---

## 🎯 REAL-WORLD EXAMPLE

### Scenario: University A Submits Annual Report

**Day 1 - 9:00 AM:**

```
Doc Officer (University A) uploads "Annual Report 2024"
Status: draft
Visible to: Doc Officer, University A Admin, Developer
```

**Day 1 - 10:00 AM:**

```
University A Admin reviews document
Clicks "Submit for MoE Review"
Status: pending
Notification sent to: MoE Admin, Developer
```

**Day 1 - 2:00 PM:**

```
MoE Admin receives notification
Goes to /approvals
Sees "Annual Report 2024" in pending list
Clicks "View Details" to review
```

**Day 1 - 3:00 PM:**

```
MoE Admin finds issues
Clicks "Request Changes"
Enters: "Please add Q4 financial data and executive summary"
Status: changes_requested
Notification sent to: Doc Officer
```

**Day 2 - 9:00 AM:**

```
Doc Officer sees notification
Views document detail page
Sees red alert: "Changes Requested: Please add Q4 financial data..."
Updates document
```

**Day 2 - 11:00 AM:**

```
University A Admin clicks "Submit for MoE Review" again
Status: pending (again)
Notification sent to: MoE Admin
```

**Day 2 - 2:00 PM:**

```
MoE Admin reviews updated document
Satisfied with changes
Clicks "Approve"
Status: approved
Notification sent to: Doc Officer
Document becomes publicly visible
```

---

## 📱 NAVIGATION MENU

The "Document Approvals" link appears in the sidebar for authorized users:

```
Sidebar Menu:
├── Dashboard
├── Documents
├── Bookmarks
├── Upload (if authorized)
├── AI Assistant
├── Document Approvals ← MoE Admin, Uni Admin, Developer
├── User Management (if admin)
├── User Approvals (if admin)
├── Institutions (if admin)
├── Analytics (if admin)
└── System Health (if developer)
```

**Icon:** CheckCircle (✓)
**Label:** "Document Approvals"
**Route:** `/approvals`

---

## ✅ SUMMARY

### MoE Review Process:

1. **University submits** → Document status = `pending`
2. **MoE receives notification** → Goes to `/approvals`
3. **MoE reviews** → Sees document details
4. **MoE decides:**
   - ✅ Approve → Document public
   - ⚠️ Request Changes → University revises
   - ❌ Reject → University fixes and resubmits
5. **University receives feedback** → Takes action

### Key Points:

- ✅ MoE ONLY sees documents explicitly submitted
- ✅ Universities maintain autonomy over drafts
- ✅ Clear feedback loop with notifications
- ✅ Status badges show document state
- ✅ Rejection reasons displayed prominently
- ✅ Can resubmit after rejection/changes

### Students:

- ❌ Students are NOT uploaders (role restriction in upload page)
- ❌ Students cannot access `/upload` route
- ❌ Students cannot submit documents for review
- ✅ Students can VIEW approved documents (based on visibility)
- ✅ Students can bookmark documents
- ✅ Students can use AI chat

**Upload page is restricted to:** Developer, MoE Admin, University Admin, Document Officer
