# OCR Review - Role-Based Access Control

## Overview
Yes, the OCR review system follows your institutional hierarchy and role-based access control. All OCR endpoints respect the same security model as the rest of your application.

## Role Hierarchy & OCR Access

### 1. Developer (Full Access)
- ✅ View all OCR results across all institutions
- ✅ Review and correct any OCR extraction
- ✅ Reprocess any document with different settings
- ✅ View OCR statistics for entire system
- ✅ Access tables from any document

### 2. Ministry Admin (Cross-Institution Oversight)
- ✅ View OCR results from all universities under their ministry
- ✅ Review and correct OCR extractions from their universities
- ✅ Reprocess documents from their universities
- ✅ View OCR statistics for their ministry
- ✅ Access tables from documents in their jurisdiction
- ❌ Cannot access OCR from other ministries

### 3. University Admin (Institution-Level)
- ✅ View OCR results from their own institution only
- ✅ Review and correct OCR extractions from their institution
- ✅ Reprocess documents from their institution
- ✅ View OCR statistics for their institution
- ✅ Access tables from their institution's documents
- ❌ Cannot access OCR from other institutions

### 4. Document Officer (Institution-Level)
- ✅ View OCR results from their own institution only
- ✅ Review and correct OCR extractions from their institution
- ✅ Reprocess documents from their institution
- ❌ Cannot view OCR statistics (admin-only feature)
- ✅ Access tables from their institution's documents
- ❌ Cannot access OCR from other institutions

### 5. Student (Read-Only)
- ✅ View OCR results for documents they have access to
- ✅ Access tables from documents they can view
- ❌ Cannot review or correct OCR extractions
- ❌ Cannot reprocess documents
- ❌ Cannot view OCR statistics

### 6. Public Viewer (Read-Only)
- ✅ View OCR results for public documents only
- ✅ Access tables from public documents
- ❌ Cannot review or correct OCR extractions
- ❌ Cannot reprocess documents
- ❌ Cannot view OCR statistics

## OCR Endpoints & Permissions

### GET `/ocr/pending-review`
**Who can access:**
- Developer (all institutions)
- Ministry Admin (their universities only)
- University Admin (their institution only)
- Document Officer (their institution only)

**Returns:** List of OCR results that need manual review

**Filtering:**
- Developer: Sees all pending reviews
- Ministry Admin: Sees reviews from universities under their ministry
- University Admin: Sees reviews from their institution
- Document Officer: Sees reviews from their institution

---

### GET `/ocr/document/{document_id}`
**Who can access:**
- Developer (any document)
- Ministry Admin (documents from their universities)
- University Admin (documents from their institution)
- Document Officer (documents from their institution)
- Student (documents they have access to)

**Returns:** OCR result for a specific document

**Access Control:**
- Checks document visibility level
- Checks institutional affiliation
- Respects document access permissions

---

### POST `/ocr/review/{ocr_id}`
**Who can access:**
- Developer (any OCR result)
- Ministry Admin (OCR from their universities)
- University Admin (OCR from their institution)
- Document Officer (OCR from their institution)

**Action:** Submit manual review/correction for OCR result

**What it does:**
1. Updates OCR result with corrected text
2. Marks OCR as reviewed (needs_review = false)
3. Updates document's extracted_text
4. Records reviewer ID and timestamp
5. Changes document ocr_status to 'completed'

**Access Control:**
- Checks institutional affiliation
- Only allows review of OCR from user's jurisdiction

---

### POST `/ocr/reprocess/{document_id}`
**Who can access:**
- Developer (any document)
- Ministry Admin (documents from their universities)
- University Admin (documents from their institution)
- Document Officer (documents from their institution)

**Action:** Re-run OCR extraction with different preprocessing settings

**Parameters:**
- `preprocessing_level`: 'light', 'medium', or 'heavy'

**What it does:**
1. Re-runs OCR with specified preprocessing level
2. Updates OCR result with new extraction
3. Updates document's extracted_text
4. Recalculates confidence and quality scores

**Access Control:**
- Only works on scanned documents
- Checks institutional affiliation
- Validates preprocessing level

---

### GET `/ocr/stats`
**Who can access:**
- Developer (system-wide stats)
- Ministry Admin (their ministry's stats)
- University Admin (their institution's stats)

**Returns:**
- Total OCR documents
- Documents needing review
- Average confidence score
- Language distribution
- Review completion rate
- Rotation corrections count
- Documents with tables count

**Filtering:**
- Developer: System-wide statistics
- Ministry Admin: Statistics for their ministry
- University Admin: Statistics for their institution

---

### GET `/ocr/tables/{document_id}`
**Who can access:**
- Developer (any document)
- Ministry Admin (documents from their universities)
- University Admin (documents from their institution)
- Document Officer (documents from their institution)
- Student (documents they have access to)

**Parameters:**
- `format`: 'json', 'markdown', 'csv', or 'html'

**Returns:** Extracted tables in requested format

**Access Control:**
- Checks document visibility level
- Checks institutional affiliation
- Respects document access permissions

## Security Features

### 1. Institutional Isolation
- Users can only access OCR results from their own institution (except Developer and Ministry Admin)
- Ministry Admin respects institutional autonomy (only sees their universities)
- No cross-institution data leakage

### 2. Role-Based Permissions
- Review/correction: Admin and Document Officer roles only
- Statistics: Admin roles only
- Reprocessing: Admin and Document Officer roles only
- Viewing: All roles (with institutional filtering)

### 3. Document Access Integration
- OCR access follows document visibility rules
- Public documents: Everyone can see OCR
- Confidential documents: Only authorized users
- Institution-only: Only users from that institution

### 4. Audit Trail
- All reviews are tracked with reviewer ID
- Review timestamps recorded
- Original OCR results preserved
- Reprocessing history maintained

## Frontend Integration

### OCR Review Page (`/ocr-review`)
**Access:**
- Developer, Ministry Admin, University Admin, Document Officer

**Features:**
- Lists documents needing OCR review
- Filtered by user's institutional access
- Shows confidence scores and issues
- Allows manual correction
- Displays extracted tables

### OCR Badge (Document Explorer)
**Visible to:** All users who can view the document

**Shows:**
- OCR status (processing, completed, needs_review, failed)
- Confidence score
- Click to open review modal (if authorized)

### OCR Review Modal
**Access:** Based on role and institutional affiliation

**Features:**
- View extracted text
- Edit and correct text (if authorized)
- View quality metrics
- View extracted tables
- Submit corrections (if authorized)

## Testing Role-Based Access

### Test as Developer:
```bash
# Login as developer
# Should see all OCR results from all institutions
GET /ocr/pending-review
```

### Test as Ministry Admin:
```bash
# Login as ministry admin
# Should only see OCR from universities under their ministry
GET /ocr/pending-review
```

### Test as University Admin:
```bash
# Login as university admin
# Should only see OCR from their institution
GET /ocr/pending-review
```

### Test as Document Officer:
```bash
# Login as document officer
# Should only see OCR from their institution
# Should NOT be able to view stats
GET /ocr/pending-review  # ✅ Works
GET /ocr/stats           # ❌ 403 Forbidden
```

### Test as Student:
```bash
# Login as student
# Should NOT be able to review OCR
GET /ocr/pending-review  # ❌ 403 Forbidden
POST /ocr/review/123     # ❌ 403 Forbidden
```

## Summary

✅ **Yes, OCR review is fully role-based and follows your hierarchy:**

1. **Institutional Isolation**: Users only see OCR from their institution (except Developer/Ministry Admin)
2. **Role Permissions**: Review/correction limited to admin and document officer roles
3. **Document Access**: OCR access follows document visibility rules
4. **Audit Trail**: All reviews tracked with user ID and timestamp
5. **Ministry Oversight**: Ministry Admin can oversee their universities' OCR
6. **Security**: No cross-institution data leakage

The OCR system integrates seamlessly with your existing role-based access control and institutional hierarchy!
