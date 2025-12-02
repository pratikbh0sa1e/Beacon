# 📊 Status Badge & Rejection Reason Visibility

## 🎯 Who Can See What and Where

---

## 1️⃣ STATUS BADGE VISIBILITY

### Where Status Badge Appears:

1. **Document Detail Page** (`/documents/{id}`)
2. **Document Explorer** (list view - if implemented)
3. **Approvals Dashboard** (`/approvals`)

### Who Can See Status Badge:

#### On Document Detail Page (`/documents/{id}`):

| User Role            | Can See Status       | Conditions                                    |
| -------------------- | -------------------- | --------------------------------------------- |
| **Developer**        | ✅ Always            | All documents                                 |
| **MoE Admin**        | ✅ If can access doc | Public, pending, or same institution          |
| **University Admin** | ✅ If can access doc | Same institution documents                    |
| **Document Officer** | ✅ If can access doc | Same institution documents                    |
| **Student**          | ✅ If can access doc | Approved documents only (based on visibility) |
| **Uploader**         | ✅ Always            | Their own documents                           |
| **Public**           | ✅ If can access doc | Public approved documents only                |

**Key Rule:** If you can see the document detail page, you can see the status badge.

---

## 2️⃣ REJECTION REASON VISIBILITY

### Where Rejection Reason Appears:

**Only on Document Detail Page** (`/documents/{id}`)

Shows as a red alert box at the top of document information when:

- Status is `rejected` OR `changes_requested`
- AND `rejection_reason` field is not empty

### Who Can See Rejection Reason:

| User Role            | Can See Rejection Reason | Conditions                                 |
| -------------------- | ------------------------ | ------------------------------------------ |
| **Developer**        | ✅ Always                | All documents                              |
| **MoE Admin**        | ✅ If can access doc     | Documents they can view                    |
| **University Admin** | ✅ If can access doc     | Same institution documents                 |
| **Document Officer** | ✅ If can access doc     | Same institution documents                 |
| **Uploader**         | ✅ Always                | Their own documents (most important)       |
| **Student**          | ❌ Usually No\*          | Students typically can't see rejected docs |
| **Public**           | ❌ No                    | Public can't see rejected docs             |

\*Students can only see approved documents, so they won't see rejected documents or rejection reasons.

---

## 3️⃣ DETAILED VISIBILITY BY STATUS

### DRAFT Documents

**Who Can See:**

- ✅ Uploader
- ✅ University Admin (same institution)
- ✅ Developer

**Status Badge:** Shows "DRAFT" (gray)
**Rejection Reason:** N/A (no rejection yet)

**Example:**

```
User: Document Officer (uploader)
Document: Their own draft
Can See: ✅ Status badge "DRAFT"
Can See: ❌ No rejection reason (not rejected)
```

---

### PENDING Documents

**Who Can See:**

- ✅ Uploader
- ✅ University Admin (same institution)
- ✅ MoE Admin (if requires_moe_approval = True)
- ✅ Developer

**Status Badge:** Shows "PENDING" (yellow)
**Rejection Reason:** N/A (not rejected yet)

**Example:**

```
User: MoE Admin
Document: Submitted for MoE review
Can See: ✅ Status badge "PENDING"
Can See: ❌ No rejection reason (not rejected)
```

---

### REJECTED Documents

**Who Can See:**

- ✅ Uploader (MOST IMPORTANT - needs to see why rejected)
- ✅ University Admin (same institution)
- ✅ MoE Admin (who rejected it)
- ✅ Developer

**Status Badge:** Shows "REJECTED" (red)
**Rejection Reason:** ✅ Shows in red alert box

**Example:**

```
User: Document Officer (uploader)
Document: Their rejected document
Can See: ✅ Status badge "REJECTED" (red)
Can See: ✅ Rejection reason in red alert box:
         "Document does not meet MoE standards..."
```

---

### CHANGES_REQUESTED Documents

**Who Can See:**

- ✅ Uploader (MOST IMPORTANT - needs to know what to change)
- ✅ University Admin (same institution)
- ✅ MoE Admin (who requested changes)
- ✅ Developer

**Status Badge:** Shows "CHANGES REQUESTED" (blue)
**Rejection Reason:** ✅ Shows in red alert box (contains requested changes)

**Example:**

```
User: University Admin
Document: From their institution
Can See: ✅ Status badge "CHANGES REQUESTED" (blue)
Can See: ✅ Changes requested in red alert box:
         "Please add Q4 financial data and executive summary"
```

---

### APPROVED Documents

**Who Can See:**

- ✅ Everyone (based on visibility level)
- Public: Everyone
- Institution-only: Same institution members
- Restricted: Admins + Doc Officers (same inst)
- Confidential: Admins only (same inst)

**Status Badge:** Shows "APPROVED" (green)
**Rejection Reason:** N/A (approved, not rejected)

**Example:**

```
User: Student
Document: Public approved document
Can See: ✅ Status badge "APPROVED" (green)
Can See: ❌ No rejection reason (not rejected)
```

---

## 4️⃣ CURRENT IMPLEMENTATION

### Document Detail Page Code:

```javascript
// Status Badge - Shows for everyone who can access the page
<Badge
  className={
    docData.approval_status === "approved"
      ? "bg-green-600"
      : docData.approval_status === "pending"
      ? "bg-yellow-600"
      : docData.approval_status === "rejected"
      ? "bg-red-600"
      : docData.approval_status === "draft"
      ? "bg-gray-600"
      : "bg-blue-600"
  }
>
  {docData.approval_status?.replace("_", " ").toUpperCase()}
</Badge>;

// Rejection Reason - Shows only when rejected or changes requested
{
  (docData.approval_status === "rejected" ||
    docData.approval_status === "changes_requested") &&
    docData.rejection_reason && (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200">
        <AlertCircle />
        <h4>
          {docData.approval_status === "rejected"
            ? "Document Rejected"
            : "Changes Requested"}
        </h4>
        <p>{docData.rejection_reason}</p>
      </div>
    );
}
```

**Current Behavior:**

- ✅ Status badge shows for everyone who can access the document
- ✅ Rejection reason shows for everyone who can access the document
- ✅ No additional filtering based on role

---

## 5️⃣ SHOULD WE RESTRICT REJECTION REASON?

### Current Implementation:

**Anyone who can see the document can see the rejection reason**

### Pros:

- ✅ Transparency
- ✅ University Admin can help uploader fix issues
- ✅ MoE Admin can see their own feedback
- ✅ Simple implementation

### Cons:

- ⚠️ Students might see rejection reasons (but they can't see rejected docs anyway)
- ⚠️ Public might see rejection reasons (but they can't see rejected docs anyway)

### Recommendation:

**Current implementation is FINE because:**

1. Rejected documents are NOT visible to students/public (filtered by approval status)
2. Only authorized users (uploader, admins) can access rejected documents
3. Rejection reason is helpful for the whole institution to understand issues

---

## 6️⃣ IF YOU WANT TO RESTRICT REJECTION REASON

If you want to show rejection reason ONLY to specific roles, here's how:

### Option A: Show Only to Uploader and Admins

```javascript
{
  /* Show rejection reason only to uploader, admins, and developer */
}
{
  (docData.approval_status === "rejected" ||
    docData.approval_status === "changes_requested") &&
    docData.rejection_reason &&
    (user?.role === "developer" ||
      user?.role === "moe_admin" ||
      user?.role === "university_admin" ||
      user?.id === docData.uploader?.id) && (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200">
        <AlertCircle />
        <h4>Document Rejected</h4>
        <p>{docData.rejection_reason}</p>
      </div>
    );
}
```

### Option B: Show Only to Uploader

```javascript
{
  /* Show rejection reason only to uploader and developer */
}
{
  (docData.approval_status === "rejected" ||
    docData.approval_status === "changes_requested") &&
    docData.rejection_reason &&
    (user?.role === "developer" || user?.id === docData.uploader?.id) && (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200">
        <AlertCircle />
        <h4>Document Rejected</h4>
        <p>{docData.rejection_reason}</p>
      </div>
    );
}
```

---

## 7️⃣ RECOMMENDED APPROACH

### Keep Current Implementation ✅

**Reason:**

1. Rejected documents are already filtered from public view
2. Only authorized users can access document detail page
3. Rejection reason helps the whole institution understand issues
4. University Admin can help Document Officer fix problems
5. Transparency within institution is good

### Access Control is Already Handled By:

1. **Document List Filtering** - Rejected docs don't appear for students/public
2. **Document Detail Access Control** - Backend checks permissions before showing document
3. **Approval Status Filter** - Students only see approved documents

---

## 8️⃣ VISIBILITY SUMMARY TABLE

### Status Badge Visibility:

| Status                | Uploader | Uni Admin (Same) | Doc Officer (Same) | MoE Admin | Student    | Public     |
| --------------------- | -------- | ---------------- | ------------------ | --------- | ---------- | ---------- |
| **Draft**             | ✅       | ✅               | ❌\*               | ❌        | ❌         | ❌         |
| **Pending**           | ✅       | ✅               | ❌\*               | ✅\*\*    | ❌         | ❌         |
| **Rejected**          | ✅       | ✅               | ❌\*               | ✅\*\*    | ❌         | ❌         |
| **Changes Requested** | ✅       | ✅               | ❌\*               | ✅\*\*    | ❌         | ❌         |
| **Approved**          | ✅       | ✅               | ✅                 | ✅\*\*\*  | ✅\*\*\*\* | ✅\*\*\*\* |

\*Unless they are the uploader  
**Only if requires_moe_approval = True  
\***Based on visibility level  
\*\*\*\*Based on visibility level (public, institution-only, etc.)

### Rejection Reason Visibility:

| Status                | Uploader | Uni Admin (Same) | Doc Officer (Same) | MoE Admin | Student | Public |
| --------------------- | -------- | ---------------- | ------------------ | --------- | ------- | ------ |
| **Rejected**          | ✅       | ✅               | ❌\*               | ✅\*\*    | ❌      | ❌     |
| **Changes Requested** | ✅       | ✅               | ❌\*               | ✅\*\*    | ❌      | ❌     |

\*Unless they are the uploader  
\*\*Only if they can access the document

---

## 9️⃣ WHERE EACH APPEARS

### Status Badge Locations:

1. **Document Detail Page** (`/documents/{id}`)

   - Next to category and visibility badges
   - In document title area
   - Color-coded for quick recognition

2. **Approvals Dashboard** (`/approvals`)

   - In document cards
   - Shows status of pending documents

3. **Document Explorer** (if implemented)
   - In document list/grid
   - Shows status of all documents

### Rejection Reason Locations:

1. **Document Detail Page ONLY** (`/documents/{id}`)

   - Red alert box at top of document information
   - Shows when status is rejected or changes_requested
   - Includes icon and formatted message

2. **Notifications**
   - Notification message includes rejection reason
   - Sent to uploader when document rejected

---

## 🎯 KEY POINTS

1. **Status Badge:**

   - ✅ Shows for everyone who can access the document
   - ✅ Color-coded for quick recognition
   - ✅ Appears on document detail page

2. **Rejection Reason:**

   - ✅ Shows for everyone who can access the document
   - ✅ Only appears when status is rejected or changes_requested
   - ✅ Formatted as prominent red alert box
   - ✅ Most important for uploader to see

3. **Access Control:**

   - ✅ Already handled by document visibility rules
   - ✅ Students/public can't see rejected documents
   - ✅ Only authorized users can access document detail page

4. **Recommendation:**
   - ✅ Keep current implementation (no additional filtering needed)
   - ✅ Rejection reason visibility is already controlled by document access
   - ✅ Transparency within institution is beneficial

---

## ✅ CONCLUSION

**Current Implementation is Correct:**

- Status badge shows for everyone who can access the document
- Rejection reason shows for everyone who can access the document
- Access control is handled by document visibility rules
- Students and public cannot see rejected documents anyway
- No additional filtering needed

**If you want stricter control:**

- Add role check to rejection reason display
- Show only to uploader, admins, and developer
- See "Option A" or "Option B" above for implementation
