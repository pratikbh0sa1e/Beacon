# Secure Document Preview Implementation

## Overview

Implemented a highly secure document preview system that prevents unauthorized downloads, copying, and printing while still allowing users to view documents.

## Security Features

### 1. **Office Online Viewer Integration**

- Uses Microsoft Office Online Viewer (`view.officeapps.live.com`) instead of Google Docs Viewer
- More restrictive - no direct download links or toolbar buttons
- Supports: PDF, DOCX, PPTX, XLSX

### 2. **Multi-Layer Protection**

#### Layer 1: Keyboard Shortcuts Disabled

- Blocks Ctrl+C (copy)
- Blocks Ctrl+P (print)
- Blocks Ctrl+S (save)
- Blocks Ctrl+A (select all)
- Blocks PrintScreen key

#### Layer 2: Context Menu Disabled

- Right-click completely disabled
- Prevents "Save As" and "Print" options

#### Layer 3: Transparent Overlay

- Invisible div layer on top of iframe
- Blocks all mouse interactions with the viewer
- Prevents clicking on any embedded buttons

#### Layer 4: CSS Protection

- `user-select: none` - prevents text selection
- `pointer-events: none` - disables mouse events on images
- `draggable={false}` - prevents drag-and-drop

#### Layer 5: Watermark

- Semi-transparent user name/email watermark
- Rotated 45 degrees across the document
- Discourages screenshots

#### Layer 6: Iframe Sandbox

- `sandbox="allow-scripts allow-same-origin"`
- Restricts iframe capabilities
- Prevents unauthorized actions

### 3. **File Type Handling**

#### PDFs & Office Documents (pdf, docx, pptx, xlsx)

- Rendered via Office Online Viewer
- Full protection layers applied
- Fallback error handling if viewer fails

#### Images (jpg, jpeg, png, gif)

- Direct image display with protection
- Watermark overlay
- Interaction blocking overlay
- Non-draggable

#### Unsupported Files (txt, etc.)

- Shows "Preview not available" message
- Explains file type limitation

## Components

### SecureDocumentViewer Component

**Location:** `frontend/src/components/documents/SecureDocumentViewer.jsx`

**Props:**

- `url` - S3 URL of the document
- `fileType` - File extension (pdf, docx, etc.)
- `userName` - User's name for watermark

**Features:**

- Automatic file type detection
- Error handling with fallback UI
- Keyboard event prevention
- Context menu blocking
- Watermark generation

### DocumentDetailPage Integration

**Location:** `frontend/src/pages/documents/DocumentDetailPage.jsx`

**Changes:**

- Imported SecureDocumentViewer component
- Replaced all iframe implementations
- Added "🔒 Protected" badge to preview title
- Passes user info for watermarking

## User Experience

### What Users CAN Do:

✅ View documents in browser
✅ Scroll through pages
✅ Zoom in/out (viewer controls)
✅ Download (only if `download_allowed` is true)

### What Users CANNOT Do:

❌ Copy text from preview
❌ Print from preview
❌ Save/download from preview
❌ Right-click on document
❌ Select text
❌ Use keyboard shortcuts
❌ Access external viewer links

## Technical Implementation

### Office Online Viewer URL Format:

```
https://view.officeapps.live.com/op/embed.aspx?src={ENCODED_URL}
```

### Protection Stack:

```
┌─────────────────────────────┐
│   Watermark (z-index: 10)   │
├─────────────────────────────┤
│ Transparent Overlay (z-20)  │
├─────────────────────────────┤
│   Sandboxed Iframe (z-0)    │
└─────────────────────────────┘
```

### Event Prevention:

```javascript
// Keyboard shortcuts
document.addEventListener("keydown", preventActions);

// Context menu
onContextMenu={(e) => e.preventDefault()}

// Drag and drop
onDragStart={(e) => e.preventDefault()}

// Copy/Cut
onCopy={(e) => e.preventDefault()}
onCut={(e) => e.preventDefault()}
```

## Limitations & Workarounds

### Known Limitations:

1. **Screenshots** - Users can still take screenshots
   - Mitigated by watermark showing user identity
2. **Screen Recording** - Users can record their screen

   - Mitigated by watermark and audit trail

3. **Mobile Devices** - Some protections may not work on mobile

   - Consider mobile-specific restrictions if needed

4. **Browser Extensions** - Some extensions might bypass protections
   - Educate users about acceptable use policies

### Future Enhancements:

- [ ] Add dynamic watermark with timestamp
- [ ] Implement view-time tracking
- [ ] Add session-based access tokens
- [ ] Consider DRM solutions for highly sensitive documents
- [ ] Add mobile-specific protections

## Testing Checklist

Test the following scenarios:

- [ ] PDF preview loads correctly
- [ ] DOCX preview loads correctly
- [ ] PPTX preview loads correctly
- [ ] Image preview loads correctly
- [ ] Right-click is disabled
- [ ] Ctrl+C doesn't copy text
- [ ] Ctrl+P doesn't open print dialog
- [ ] Ctrl+S doesn't save file
- [ ] Text selection is disabled
- [ ] Watermark is visible
- [ ] Download button only shows when `download_allowed=true`
- [ ] Error handling works for invalid URLs
- [ ] Unsupported file types show appropriate message

## Security Best Practices

1. **Always use HTTPS** - Ensure S3 URLs use HTTPS
2. **Signed URLs** - Consider using time-limited signed URLs
3. **Access Control** - Backend validates user permissions
4. **Audit Logging** - Log all document access attempts
5. **User Education** - Inform users about acceptable use policies

## Conclusion

This implementation provides strong protection against casual copying and downloading while maintaining a good user experience. For documents requiring maximum security, consider additional measures like DRM or converting documents to images server-side.
