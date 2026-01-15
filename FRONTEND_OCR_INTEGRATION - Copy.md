# 🎨 Frontend OCR Integration Guide

## ✅ What's Been Created

### Components Created

1. **OCRBadge.jsx** - Shows OCR status, confidence, rotation, and tables
2. **OCRReviewModal.jsx** - Modal for reviewing and correcting OCR text
3. **TableViewer.jsx** - View and download extracted tables
4. **OCRReviewPage.jsx** - Full page for managing OCR reviews

### File Locations

```
frontend/src/
├── components/ocr/
│   ├── OCRBadge.jsx           # Status badges
│   ├── OCRReviewModal.jsx     # Review interface
│   ├── TableViewer.jsx        # Table viewer
│   └── index.js               # Exports
└── pages/
    └── OCRReviewPage.jsx      # Review queue page
```

---

## 🚀 Integration Steps

### Step 1: Add Route for OCR Review Page

**File:** `frontend/src/App.jsx`

```jsx
import OCRReviewPage from './pages/OCRReviewPage';

// Add to your routes
<Route path="/ocr-review" element={<OCRReviewPage />} />
```

### Step 2: Add OCR Badge to Document Cards

**File:** `frontend/src/components/documents/DocumentCard.jsx` (or similar)

```jsx
import { OCRBadge } from '@/components/ocr';

const DocumentCard = ({ document }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{document.filename}</CardTitle>
        
        {/* Add OCR Badge */}
        <OCRBadge document={document} />
      </CardHeader>
      {/* Rest of card */}
    </Card>
  );
};
```

### Step 3: Add Review Button for Low-Confidence Documents

**File:** `frontend/src/components/documents/DocumentCard.jsx`

```jsx
import { OCRReviewModal, TableViewer } from '@/components/ocr';
import { useState } from 'react';

const DocumentCard = ({ document }) => {
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [showTableViewer, setShowTableViewer] = useState(false);

  return (
    <Card>
      {/* ... */}
      
      {/* Show review button if needs review */}
      {document.needs_ocr_review && (
        <Button 
          variant="outline" 
          size="sm"
          onClick={() => setShowReviewModal(true)}
        >
          <AlertCircle className="w-4 h-4 mr-1" />
          Review OCR
        </Button>
      )}
      
      {/* Show tables button if has tables */}
      {document.has_tables && (
        <Button 
          variant="outline" 
          size="sm"
          onClick={() => setShowTableViewer(true)}
        >
          <Table className="w-4 h-4 mr-1" />
          View Tables ({document.tables_found})
        </Button>
      )}

      {/* Modals */}
      <OCRReviewModal
        isOpen={showReviewModal}
        onClose={() => setShowReviewModal(false)}
        documentId={document.id}
        onReviewComplete={() => {
          // Refresh document list
        }}
      />
      
      <TableViewer
        isOpen={showTableViewer}
        onClose={() => setShowTableViewer(false)}
        documentId={document.id}
        documentName={document.filename}
      />
    </Card>
  );
};
```

### Step 4: Add Navigation Link

**File:** `frontend/src/components/layout/Sidebar.jsx` (or Navigation)

```jsx
import { FileSearch } from 'lucide-react';

// Add to navigation items
{
  name: 'OCR Review',
  href: '/ocr-review',
  icon: FileSearch,
  badge: ocrReviewCount, // Optional: show count
  roles: ['developer', 'MINISTRY_ADMIN', 'university_admin', 'document_officer']
}
```

### Step 5: Show OCR Info in Document Upload Response

**File:** `frontend/src/components/documents/DocumentUpload.jsx`

```jsx
const handleUploadComplete = (response) => {
  const result = response.results[0];
  
  if (result.is_scanned) {
    toast.success(
      <div>
        <p>Document uploaded successfully!</p>
        <p className="text-sm mt-1">
          OCR Confidence: {Math.round(result.ocr_confidence * 100)}%
        </p>
        {result.rotation_corrected && (
          <p className="text-sm">Rotation corrected: {result.rotation_corrected}°</p>
        )}
        {result.has_tables && (
          <p className="text-sm">Tables found: {result.tables_found}</p>
        )}
        {result.needs_ocr_review && (
          <p className="text-sm text-orange-600">⚠️ Manual review recommended</p>
        )}
      </div>
    );
  }
};
```

---

## 📊 Component Usage Examples

### Example 1: Simple Badge Display

```jsx
import { OCRBadge } from '@/components/ocr';

<OCRBadge document={document} />
```

**Shows:**
- ✅ OCR status badge
- 📊 Confidence percentage
- 🔄 Rotation angle (if corrected)
- 📋 Number of tables (if found)
- ⚠️ Review needed indicator

### Example 2: Review Modal

```jsx
import { OCRReviewModal } from '@/components/ocr';

const [showModal, setShowModal] = useState(false);

<OCRReviewModal
  isOpen={showModal}
  onClose={() => setShowModal(false)}
  documentId={123}
  onReviewComplete={() => {
    console.log('Review submitted!');
    // Refresh your document list
  }}
/>
```

**Features:**
- View OCR metadata (confidence, language, quality)
- See detected issues
- Edit extracted text
- Reprocess with different settings (light/medium/heavy)
- Submit corrections with notes

### Example 3: Table Viewer

```jsx
import { TableViewer } from '@/components/ocr';

const [showTables, setShowTables] = useState(false);

<TableViewer
  isOpen={showTables}
  onClose={() => setShowTables(false)}
  documentId={123}
  documentName="policy_document.pdf"
/>
```

**Features:**
- View tables in 4 formats (Table, Markdown, CSV, HTML)
- Download individual tables
- See page numbers
- Responsive table display

### Example 4: Full Review Page

```jsx
import OCRReviewPage from '@/pages/OCRReviewPage';

// Add to routes
<Route path="/ocr-review" element={<OCRReviewPage />} />
```

**Features:**
- List all documents needing review
- Search and filter
- View OCR statistics
- Quick review access
- Batch processing

---

## 🎨 Styling Notes

All components use:
- **shadcn/ui** components (Button, Card, Dialog, etc.)
- **Tailwind CSS** for styling
- **Lucide React** for icons
- **Dark mode** support built-in

### Required shadcn/ui Components

Make sure you have these installed:

```bash
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add badge
npx shadcn-ui@latest add input
npx shadcn-ui@latest add textarea
npx shadcn-ui@latest add tabs
npx shadcn-ui@latest add tooltip
npx shadcn-ui@latest add alert
```

---

## 🔌 API Integration

All components use the existing `api` service:

```javascript
import api from '@/services/api';

// Get pending reviews
const response = await api.get('/ocr/pending-review');

// Get OCR data for document
const response = await api.get(`/ocr/document/${documentId}`);

// Submit review
await api.post(`/ocr/review/${ocrId}`, {
  corrected_text: text,
  notes: notes
});

// Reprocess document
await api.post(`/ocr/reprocess/${documentId}`, {
  preprocessing_level: 'heavy'
});

// Get tables
const response = await api.get(`/ocr/tables/${documentId}?format=markdown`);

// Get stats
const response = await api.get('/ocr/stats');
```

---

## 📱 Responsive Design

All components are mobile-responsive:

- **OCRBadge**: Wraps badges on small screens
- **OCRReviewModal**: Scrollable on mobile
- **TableViewer**: Horizontal scroll for wide tables
- **OCRReviewPage**: Stacks cards on mobile

---

## 🎯 User Flows

### Flow 1: Upload Scanned Document

1. User uploads PDF
2. Backend processes with OCR
3. Upload response shows OCR info
4. If low confidence → Badge shows "Review Needed"
5. User clicks "Review OCR" button
6. Modal opens with extracted text
7. User corrects text and submits
8. Document updated, badge changes to "Completed"

### Flow 2: View Extracted Tables

1. User sees document with tables badge
2. Clicks "View Tables" button
3. TableViewer modal opens
4. User switches between formats (JSON/Markdown/CSV/HTML)
5. User downloads table in preferred format

### Flow 3: Bulk Review

1. Admin navigates to `/ocr-review`
2. Sees list of all documents needing review
3. Views stats (total, pending, completion rate)
4. Searches for specific document
5. Clicks "Review & Correct" on document
6. Reviews and submits corrections
7. Document removed from queue

---

## 🐛 Troubleshooting

### Issue: Components not rendering

**Solution:** Check imports and ensure shadcn/ui components are installed

```bash
npx shadcn-ui@latest add dialog button card badge
```

### Issue: API calls failing

**Solution:** Verify backend is running and API base URL is correct

```javascript
// Check frontend/.env
VITE_API_BASE_URL=http://localhost:8000/api
```

### Issue: Badges not showing

**Solution:** Ensure document object has OCR fields:

```javascript
{
  is_scanned: true,
  ocr_status: 'completed',
  ocr_confidence: 0.92,
  rotation_corrected: 90,
  tables_found: 3,
  has_tables: true,
  needs_ocr_review: false
}
```

---

## ✅ Testing Checklist

- [ ] OCRBadge displays correctly on document cards
- [ ] Review modal opens and loads OCR data
- [ ] Text editing works in review modal
- [ ] Reprocess buttons trigger correctly
- [ ] Table viewer shows tables in all formats
- [ ] Table download works
- [ ] OCR Review page loads pending documents
- [ ] Search and filter work
- [ ] Stats display correctly
- [ ] Mobile responsive on all screens
- [ ] Dark mode works properly

---

## 🚀 Quick Start

1. **Add route:**
```jsx
<Route path="/ocr-review" element={<OCRReviewPage />} />
```

2. **Add to document card:**
```jsx
import { OCRBadge } from '@/components/ocr';
<OCRBadge document={document} />
```

3. **Add navigation link:**
```jsx
{ name: 'OCR Review', href: '/ocr-review', icon: FileSearch }
```

4. **Test upload:**
- Upload a scanned PDF
- Check for OCR badges
- Click "Review OCR" if needed
- View tables if available

**That's it! Your frontend is now OCR-ready! 🎉**

---

## 📚 Additional Resources

- Backend API Docs: http://localhost:8000/docs
- OCR Feature Docs: `OCR_FEATURE_DOCUMENTATION.md`
- shadcn/ui Docs: https://ui.shadcn.com/
- Tailwind CSS: https://tailwindcss.com/

---

**Version:** 1.0.0  
**Last Updated:** December 8, 2025  
**Status:** ✅ Ready for Integration
