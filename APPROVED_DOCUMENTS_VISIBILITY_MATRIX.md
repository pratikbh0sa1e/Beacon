# 📊 APPROVED DOCUMENTS - Complete Visibility Matrix

## 🎯 Overview

Once a document is **APPROVED** (`approval_status = "approved"`), visibility is determined by:

1. **Visibility Level** (public, institution_only, restricted, confidential)
2. **Viewer's Role** (developer, moe_admin, university_admin, document_officer, student, public)
3. **Viewer's Institution** (same or different from document's institution)

---

## 📋 VISIBILITY LEVEL BREAKDOWN

### 1. PUBLIC Documents (Approved)

**Rule:** Everyone can see, regardless of role or institution

| Viewer Role          | Same Institution | Different Institution | No Institution |
| -------------------- | ---------------- | --------------------- | -------------- |
| **Developer**        | ✅ Can See       | ✅ Can See            | ✅ Can See     |
| **MoE Admin**        | ✅ Can See       | ✅ Can See            | ✅ Can See     |
| **University Admin** | ✅ Can See       | ✅ Can See            | ✅ Can See     |
| **Document Officer** | ✅ Can See       | ✅ Can See            | ✅ Can See     |
| **Student**          | ✅ Can See       | ✅ Can See            | ✅ Can See     |
| **Public Viewer**    | ✅ Can See       | ✅ Can See            | ✅ Can See     |

**Summary:** PUBLIC = Everyone sees it ✅

---

### 2. INSTITUTION-ONLY Documents (Approved)

**Rule:** Only members of the same institution can see

| Viewer Role          | Same Institution | Different Institution | No Institution |
| -------------------- | ---------------- | --------------------- | -------------- |
| **Developer**        | ✅ Can See       | ✅ Can See            | ✅ Can See     |
| **MoE Admin**        | ✅ Can See       | ❌ Cannot See         | ❌ Cannot See  |
| **University Admin** | ✅ Can See       | ❌ Cannot See         | ❌ Cannot See  |
| **Document Officer** | ✅ Can See       | ❌ Cannot See         | ❌ Cannot See  |
| **Student**          | ✅ Can See       | ❌ Cannot See         | ❌ Cannot See  |
| **Public Viewer**    | ❌ Cannot See    | ❌ Cannot See         | ❌ Cannot See  |

**Summary:** Only same institution members + Developer ✅

---

### 3. RESTRICTED Documents (Approved)

**Rule:** Only admins and document officers from same institution

| Viewer Role          | Same Institution | Different Institution | No Institution |
| -------------------- | ---------------- | --------------------- | -------------- |
| **Developer**        | ✅ Can See       | ✅ Can See            | ✅ Can See     |
| **MoE Admin**        | ✅ Can See       | ❌ Cannot See         | ❌ Cannot See  |
| **University Admin** | ✅ Can See       | ❌ Cannot See         | ❌ Cannot See  |
| **Document Officer** | ✅ Can See       | ❌ Cannot See         | ❌ Cannot See  |
| **Student**          | ❌ Cannot See    | ❌ Cannot See         | ❌ Cannot See  |
| **Public Viewer**    | ❌ Cannot See    | ❌ Cannot See         | ❌ Cannot See  |

**Summary:** Admins + Doc Officers (same institution) + Developer ✅

---

### 4. CONFIDENTIAL Documents (Approved)

**Rule:** Only admins from same institution (highest security)

| Viewer Role          | Same Institution | Different Institution | No Institution |
| -------------------- | ---------------- | --------------------- | -------------- |
| **Developer**        | ✅ Can See       | ✅ Can See            | ✅ Can See     |
| **MoE Admin**        | ✅ Can See       | ❌ Cannot See         | ❌ Cannot See  |
| **University Admin** | ✅ Can See       | ❌ Cannot See         | ❌ Cannot See  |
| **Document Officer** | ❌ Cannot See\*  | ❌ Cannot See         | ❌ Cannot See  |
| **Student**          | ❌ Cannot See    | ❌ Cannot See         | ❌ Cannot See  |
| **Public Viewer**    | ❌ Cannot See    | ❌ Cannot See         | ❌ Cannot See  |

\*Unless they are the uploader (ownership rule)

**Summary:** Only Admins (same institution) + Developer ✅

---

## 👤 BY UPLOADER ROLE - All Cases

### CASE 1: Developer Uploads Document

#### Scenario: Developer uploads a document to University A

| Visibility           | Developer | MoE Admin | Uni A Admin | Uni B Admin | Doc Officer A | Student A | Public |
| -------------------- | --------- | --------- | ----------- | ----------- | ------------- | --------- | ------ |
| **Public**           | ✅        | ✅        | ✅          | ✅          | ✅            | ✅        | ✅     |
| **Institution-Only** | ✅        | ❌        | ✅          | ❌          | ✅            | ✅        | ❌     |
| **Restricted**       | ✅        | ❌        | ✅          | ❌          | ✅            | ❌        | ❌     |
| **Confidential**     | ✅        | ❌        | ✅          | ❌          | ❌            | ❌        | ❌     |

**Key Points:**

- Developer can upload to any institution
- Document follows normal visibility rules
- Developer always has access (god mode)

---

### CASE 2: MoE Admin Uploads Document

#### Scenario: MoE Admin uploads to MoE institution

| Visibility           | Developer | MoE Admin | Uni A Admin | Doc Officer MoE | Student MoE | Public |
| -------------------- | --------- | --------- | ----------- | --------------- | ----------- | ------ |
| **Public**           | ✅        | ✅        | ✅          | ✅              | ✅          | ✅     |
| **Institution-Only** | ✅        | ✅        | ❌          | ✅              | ✅          | ❌     |
| **Restricted**       | ✅        | ✅        | ❌          | ✅              | ❌          | ❌     |
| **Confidential**     | ✅        | ✅        | ❌          | ❌              | ❌          | ❌     |

**Key Points:**

- MoE Admin uploads to their own institution
- Other MoE Admins can see (same institution)
- Universities cannot see (unless public)
- Follows institutional boundaries

---

### CASE 3: University Admin Uploads Document

#### Scenario: University A Admin uploads to University A

| Visibility           | Developer | MoE Admin | Uni A Admin | Uni B Admin | Doc Officer A | Student A | Public |
| -------------------- | --------- | --------- | ----------- | ----------- | ------------- | --------- | ------ |
| **Public**           | ✅        | ✅        | ✅          | ✅          | ✅            | ✅        | ✅     |
| **Institution-Only** | ✅        | ❌        | ✅          | ❌          | ✅            | ✅        | ❌     |
| **Restricted**       | ✅        | ❌        | ✅          | ❌          | ✅            | ❌        | ❌     |
| **Confidential**     | ✅        | ❌        | ✅          | ❌          | ❌            | ❌        | ❌     |

**Key Points:**

- **MoE Admin CANNOT see** (unless public or submitted for review)
- Only University A members can see
- **Institutional Autonomy Protected** ✅
- This is the most common case

---

### CASE 4: Document Officer Uploads Document

#### Scenario: Document Officer from University A uploads

| Visibility           | Developer | MoE Admin | Uni A Admin | Uni B Admin | Doc Officer A | Student A | Public |
| -------------------- | --------- | --------- | ----------- | ----------- | ------------- | --------- | ------ |
| **Public**           | ✅        | ✅        | ✅          | ✅          | ✅            | ✅        | ✅     |
| **Institution-Only** | ✅        | ❌        | ✅          | ❌          | ✅            | ✅        | ❌     |
| **Restricted**       | ✅        | ❌        | ✅          | ❌          | ✅            | ❌        | ❌     |
| **Confidential**     | ✅        | ❌        | ✅          | ❌          | ✅\*          | ❌        | ❌     |

\*Doc Officer can see confidential ONLY if they are the uploader (ownership rule)

**Key Points:**

- Same as University Admin case
- **MoE Admin CANNOT see** (unless public)
- Doc Officer can see their own confidential uploads
- Institutional privacy maintained

---

### CASE 5: Student Uploads Document

#### Scenario: Student from University A uploads (if allowed)

| Visibility           | Developer | MoE Admin | Uni A Admin | Uni B Admin | Doc Officer A | Student A | Public |
| -------------------- | --------- | --------- | ----------- | ----------- | ------------- | --------- | ------ |
| **Public**           | ✅        | ✅        | ✅          | ✅          | ✅            | ✅        | ✅     |
| **Institution-Only** | ✅        | ❌        | ✅          | ❌          | ✅            | ✅        | ❌     |
| **Restricted**       | ✅        | ❌        | ✅          | ❌          | ✅            | ❌        | ❌     |
| **Confidential**     | ✅        | ❌        | ✅          | ❌          | ❌            | ❌        | ❌     |

**Key Points:**

- Students typically cannot upload (role restriction)
- If allowed, follows same rules as Document Officer
- **MoE Admin CANNOT see** (unless public)

---

## 🔐 SPECIAL RULES

### 1. Uploader Ownership Rule

**Rule:** Uploader ALWAYS has access to their own documents, regardless of visibility

**Example:**

- Document Officer uploads CONFIDENTIAL document
- Normally, Doc Officers cannot see confidential
- BUT uploader can see their own document ✅

### 2. Developer God Mode

**Rule:** Developer can see ALL documents, regardless of:

- Visibility level
- Institution
- Approval status
- Any other restriction

### 3. MoE Admin Institutional Autonomy

**Rule:** MoE Admin CANNOT see university documents unless:

- Document is PUBLIC (approved)
- Document is PENDING approval (`requires_moe_approval = True`)
- Document is from MoE's own institution
- MoE Admin is the uploader

**This is the KEY principle of Option 2** ✅

---

## 📊 COMPLETE MATRIX: All Combinations

### PUBLIC Documents (Approved)

| Uploader Role | Developer | MoE Admin | Uni Admin (Same) | Uni Admin (Diff) | Doc Officer (Same) | Student (Same) | Public |
| ------------- | --------- | --------- | ---------------- | ---------------- | ------------------ | -------------- | ------ |
| Developer     | ✅        | ✅        | ✅               | ✅               | ✅                 | ✅             | ✅     |
| MoE Admin     | ✅        | ✅        | ✅               | ✅               | ✅                 | ✅             | ✅     |
| Uni Admin     | ✅        | ✅        | ✅               | ✅               | ✅                 | ✅             | ✅     |
| Doc Officer   | ✅        | ✅        | ✅               | ✅               | ✅                 | ✅             | ✅     |
| Student       | ✅        | ✅        | ✅               | ✅               | ✅                 | ✅             | ✅     |

**Result:** Everyone sees PUBLIC documents ✅

---

### INSTITUTION-ONLY Documents (Approved)

| Uploader Role | Developer | MoE Admin | Uni Admin (Same) | Uni Admin (Diff) | Doc Officer (Same) | Student (Same) | Public |
| ------------- | --------- | --------- | ---------------- | ---------------- | ------------------ | -------------- | ------ |
| Developer     | ✅        | ❌        | ✅               | ❌               | ✅                 | ✅             | ❌     |
| MoE Admin     | ✅        | ✅        | ❌               | ❌               | ❌                 | ❌             | ❌     |
| Uni Admin     | ✅        | ❌        | ✅               | ❌               | ✅                 | ✅             | ❌     |
| Doc Officer   | ✅        | ❌        | ✅               | ❌               | ✅                 | ✅             | ❌     |
| Student       | ✅        | ❌        | ✅               | ❌               | ✅                 | ✅             | ❌     |

**Result:** Only same institution members ✅

---

### RESTRICTED Documents (Approved)

| Uploader Role | Developer | MoE Admin | Uni Admin (Same) | Uni Admin (Diff) | Doc Officer (Same) | Student (Same) | Public |
| ------------- | --------- | --------- | ---------------- | ---------------- | ------------------ | -------------- | ------ |
| Developer     | ✅        | ❌        | ✅               | ❌               | ✅                 | ❌             | ❌     |
| MoE Admin     | ✅        | ✅        | ❌               | ❌               | ❌                 | ❌             | ❌     |
| Uni Admin     | ✅        | ❌        | ✅               | ❌               | ✅                 | ❌             | ❌     |
| Doc Officer   | ✅        | ❌        | ✅               | ❌               | ✅                 | ❌             | ❌     |
| Student       | ✅        | ❌        | ✅               | ❌               | ✅                 | ❌             | ❌     |

**Result:** Admins + Doc Officers (same institution) ✅

---

### CONFIDENTIAL Documents (Approved)

| Uploader Role | Developer | MoE Admin | Uni Admin (Same) | Uni Admin (Diff) | Doc Officer (Same) | Student (Same) | Public |
| ------------- | --------- | --------- | ---------------- | ---------------- | ------------------ | -------------- | ------ |
| Developer     | ✅        | ❌        | ✅               | ❌               | ❌                 | ❌             | ❌     |
| MoE Admin     | ✅        | ✅        | ❌               | ❌               | ❌                 | ❌             | ❌     |
| Uni Admin     | ✅        | ❌        | ✅               | ❌               | ❌                 | ❌             | ❌     |
| Doc Officer   | ✅        | ❌        | ✅               | ❌               | ✅\*               | ❌             | ❌     |
| Student       | ✅        | ❌        | ✅               | ❌               | ❌                 | ❌             | ❌     |

\*Doc Officer can see ONLY if they are the uploader

**Result:** Only Admins (same institution) + Uploader ✅

---

## 🎯 KEY TAKEAWAYS

### 1. PUBLIC = Everyone

- No restrictions
- All roles can see
- All institutions can see

### 2. INSTITUTION-ONLY = Same Institution Members

- Developer ✅
- Same institution: All roles ✅
- Different institution: Nobody ❌
- MoE Admin: Only if same institution ✅

### 3. RESTRICTED = Admins + Doc Officers (Same Institution)

- Developer ✅
- Same institution: Admins + Doc Officers ✅
- Same institution: Students ❌
- Different institution: Nobody ❌

### 4. CONFIDENTIAL = Admins Only (Same Institution)

- Developer ✅
- Same institution: Admins only ✅
- Same institution: Doc Officers ❌ (unless uploader)
- Different institution: Nobody ❌

### 5. MoE Admin Special Rule

**MoE Admin CANNOT see university documents unless:**

- ✅ Document is PUBLIC
- ✅ Document is PENDING approval
- ✅ Document is from MoE's institution
- ✅ MoE Admin uploaded it

**This protects institutional autonomy** 🔒

---

## 📝 REAL-WORLD EXAMPLES

### Example 1: University Timetable

```
Uploader: University A Admin
Visibility: institution_only
Status: approved

Who can see:
✅ Developer
✅ University A Admin
✅ University A Doc Officers
✅ University A Students
❌ MoE Admin (institutional privacy)
❌ University B members
❌ Public
```

### Example 2: Public Announcement

```
Uploader: MoE Admin
Visibility: public
Status: approved

Who can see:
✅ Everyone (all roles, all institutions, public)
```

### Example 3: Confidential Budget Report

```
Uploader: University A Admin
Visibility: confidential
Status: approved

Who can see:
✅ Developer
✅ University A Admin
❌ MoE Admin (institutional privacy)
❌ University A Doc Officers
❌ University A Students
❌ Everyone else
```

### Example 4: Policy Document for Review

```
Uploader: University A Admin
Visibility: restricted
Status: approved

Who can see:
✅ Developer
✅ University A Admin
✅ University A Doc Officers
❌ MoE Admin (institutional privacy)
❌ University A Students
❌ University B members
```

---

## ✅ SUMMARY TABLE

| Visibility           | Developer | MoE (Same Inst) | MoE (Diff Inst) | Uni Admin (Same) | Doc Officer (Same) | Student (Same) | Public |
| -------------------- | --------- | --------------- | --------------- | ---------------- | ------------------ | -------------- | ------ |
| **Public**           | ✅        | ✅              | ✅              | ✅               | ✅                 | ✅             | ✅     |
| **Institution-Only** | ✅        | ✅              | ❌              | ✅               | ✅                 | ✅             | ❌     |
| **Restricted**       | ✅        | ✅              | ❌              | ✅               | ✅                 | ❌             | ❌     |
| **Confidential**     | ✅        | ✅              | ❌              | ✅               | ❌\*               | ❌             | ❌     |

\*Unless uploader

**Remember:** This applies ONLY to APPROVED documents. Draft/Pending documents have different rules!
