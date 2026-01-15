# BEACON - Workflows and Features Guide

## Comprehensive Feature Documentation

**Version**: 2.0.0  
**Last Updated**: December 4, 2025

---

## 📋 Table of Contents

1. [User Registration & Approval Workflow](#1-user-registration--approval-workflow)
2. [Document Upload & Approval Workflow](#2-document-upload--approval-workflow)
3. [AI Chat & RAG System](#3-ai-chat--rag-system)
4. [Voice Query System](#4-voice-query-system)
5. [Notification System](#5-notification-system)
6. [Institution Management](#6-institution-management)
7. [External Data Source Integration](#7-external-data-source-integration)
8. [Analytics & Insights](#8-analytics--insights)

---

## 1. User Registration & Approval Workflow

### Registration Process

**Step 1: User Registration**

- User fills registration form (name, email, password, role, institution)
- Email validated against institution domains
- Account created with `approved=False`

**Step 2: Email Verification**

- System sends verification email
- User clicks verification link
- Email verified, account moves to "Pending Approval"

**Step 3: Admin Approval**

| User Role Registering | Approver         | Notification Sent To                          |
| --------------------- | ---------------- | --------------------------------------------- |
| Student               | University Admin | University Admin + Ministry Admin + Developer |
| Document Officer      | University Admin | University Admin + Ministry Admin + Developer |
| University Admin      | Ministry Admin   | Ministry Admin + Developer                    |
| Ministry Admin        | Developer        | Developer                                     |

**Step 4: Approval Actions**

- **Approve**: Admin reviews, clicks approve, user can login
- **Reject**: Admin provides reason, user notified
- **Revoke**: Admin can revoke previously approved user

### Role Change Workflow

- Admin navigates to User Management
- Selects user, changes role
- Audit log created, user notified
- Permissions updated immediately

**Restrictions**:

- Cannot change Developer role
- Maximum 5 Ministry Admins
- 1 University Admin per institution

---

## 2. Document Upload & Approval Workflow

### Upload Process

**Step 1: Document Upload**

- User selects file (PDF, DOCX, PPTX, Image)
- Fills metadata (title, description, category, visibility, expiry)
- Clicks "Upload"

**Step 2: Processing**

- Backend validates file
- Extracts text (with OCR if needed)
- Uploads to Supabase S3
- Saves metadata to PostgreSQL
- Returns success (3-7 seconds)
- Background: AI extracts metadata

**Step 3: Approval Status Assignment**

| Uploader Role    | Visibility Level | Initial Status | Requires Approval From |
| ---------------- | ---------------- | -------------- | ---------------------- |
| Developer        | Any              | Approved       | None (auto-approved)   |
| Ministry Admin   | Any              | Approved       | None (auto-approved)   |
| University Admin | Any              | Pending        | Ministry Admin         |
| Document Officer | Any              | Pending        | University Admin       |
| Student          | Any              | Pending        | University Admin       |

### Approval Process

**Admin Reviews Pending Documents**:

- Views list of pending documents
- Filters by visibility, uploader, date, institution
- Searches by filename or uploader name

**Document Review**:

- Views document details
- Can preview document
- Sees uploader information, metadata

**Approval Actions**:

- **Approve**: Optional notes, document becomes visible
- **Reject**: Required reason, document hidden
- **Request Changes**: Specify changes needed, uploader can resubmit

### Document Visibility Rules

| Visibility Level | Visible To                | Searchable By             | RAG Access                |
| ---------------- | ------------------------- | ------------------------- | ------------------------- |
| Public           | All authenticated users   | All users                 | All users                 |
| Institution Only | Same institution users    | Same institution          | Same institution          |
| Restricted       | Ministry Admin, Developer | Ministry Admin, Developer | Ministry Admin, Developer |
| Confidential     | Developer only            | Developer only            | Developer only            |

### Document Lifecycle

```
Draft → Pending → Under Review → Approved
                              ↓
                         Changes Requested → Pending (resubmit)
                              ↓
                          Rejected → Archived
```

---

## 3. AI Chat & RAG System

### Query Process

**Step 1: User Asks Question**

- User types question in natural language
- Question sent to backend with user context

**Step 2: RAG Pipeline**

```
1. Query Received
2. User Context Extracted (role, institution_id)
3. Metadata Search (BM25) - Filters by permissions
4. Check Embedding Status
5. Lazy Embedding (if needed) - Chunks + BGE-M3
6. Vector Search - pgvector with role filters
7. Hybrid Reranking - BM25 (30%) + Vector (70%)
8. RAG Agent (Gemini) - ReAct framework
9. Response Returned - Answer + Citations + Confidence
```

### Role-Based Access in RAG

**Developer**: Sees ALL documents
**Ministry Admin**: Sees public, restricted, all institution_only
**University Admin**: Sees public + own institution
**Student**: Sees public + own institution's approved docs

### Chat History

- Unlimited chat sessions per user
- Full conversation history
- Search within chat history
- Export chat to PDF/TXT

---

## 4. Voice Query System

### Voice Query Process

**Step 1: Audio Recording**

- User records audio or uploads file
- Supported: MP3, WAV, M4A, OGG, FLAC

**Step 2: Transcription**

- Detects language (auto or user-specified)
- Transcribes using Whisper (local) or Google Speech (cloud)
- Processing: 5-10 seconds for 1 min audio

**Step 3: Query Processing**

- Transcribed text → RAG pipeline
- Returns answer with citations

**Step 4: Response**

- Transcription text (for verification)
- AI answer + citations + confidence

### Supported Languages

98+ languages including English, Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi, Urdu, Spanish, French, German, Chinese, Japanese, Arabic

### Voice Engines

- **Whisper (Local)**: Free, private, GPU-accelerated
- **Google Cloud Speech**: Cloud-based, high quality, paid

---

## 5. Notification System

### Hierarchical Routing

```
Student Action → University Admin (same institution)
                 ↓
              Ministry Admin
                 ↓
              Developer (sees all)
```

### Priority Levels

| Priority    | Icon   | Use Cases                        | Duration |
| ----------- | ------ | -------------------------------- | -------- |
| 🔥 Critical | Red    | Security alerts, system failures | 10s      |
| ⚠ High      | Orange | Approval requests, role changes  | 7s       |
| 📌 Medium   | Blue   | Upload confirmations, reminders  | 5s       |
| 📨 Low      | Gray   | General info, read receipts      | 3s       |

### Notification Types

- user_approval, document_approval, role_change
- system_alert, upload_success, approval_granted
- approval_denied, embedding_failed

### Features

- Grouped by priority (collapsible sections)
- Badge counts, mark read/unread
- Filters (all, unread, by priority, by type)
- Action buttons (Approve Now, Review, etc.)
- Real-time updates (polling every 30s)
- Toast notifications with color coding

---

## 6. Institution Management

### Institution Types

- **Ministry**: Parent organization (e.g., Ministry of Education)
- **University**: Educational institution linked to ministry

### Institution Workflow

**Create Institution**:

- Admin fills form (name, location, type, parent ministry)
- Institution created, audit log created

**Add Email Domain**:

- Admin adds domain (e.g., "mit.edu")
- Only users with @mit.edu can register for this institution

**Edit Institution**:

- Admin updates fields
- Changes applied, audit log created

**Delete Institution** (Soft Delete):

- Confirmation dialog shows users/documents count
- Institution marked as deleted (deleted_at timestamp)
- Users reassigned, documents preserved but hidden

### Domain Validation

- User enters email during registration
- System checks institution_domains table
- If match: Institution auto-selected
- If no match: User selects "Other", admin approval required

---

## 7. External Data Source Integration

### Request Workflow

**Step 1: Submit Request**

- Ministry/University Admin fills form:
  - Name, ministry, description
  - Database connection details
  - Table/column configuration
  - Storage type (database BLOB or Supabase)
  - Data classification (public, educational, confidential, institutional)
- Tests connection, submits request

**Step 2: Developer Review**

- Developer receives notification
- Reviews details, tests connection
- Decides: Approve or Reject

**Step 3: Approval**

- Data source activated
- Auto-sync triggered immediately
- Scheduled sync enabled (daily at 2 AM)
- Requester notified

**Step 4: Rejection**

- Required: Provide rejection reason
- Credentials deleted (security)
- Requester notified with reason

### Sync Process

**Automatic Sync** (Daily at 2 AM):

1. Connect to database
2. Query table for new/updated documents
3. Fetch file data
4. Extract text
5. Upload to Supabase S3
6. Save metadata to PostgreSQL
7. Set visibility based on classification
8. Log sync results
9. Send notification on completion

**Manual Sync**:

- Developer clicks "Sync Now"
- Optional: Set limit
- Progress shown, completion notification

### Data Classification

| Classification | Visibility Level | Access                    |
| -------------- | ---------------- | ------------------------- |
| Public         | public           | All users                 |
| Educational    | public           | All users                 |
| Confidential   | restricted       | Ministry Admin, Developer |
| Institutional  | institution_only | Same institution users    |

---

## 8. Analytics & Insights

### System Health Dashboard (Developer Only)

**Components**:

- Database Status (connection, response time, active connections)
- S3 Storage (connection, total files, storage used)
- Vector Store (total embeddings, indexed documents, avg time)
- LLM (API status, avg response time, requests today)
- Overall Health (✅ Healthy / ⚠ Degraded / ❌ Critical)

### Analytics Dashboard (Admin Roles)

**Stats Cards**:

- Total Documents, Users, Institutions, Pending Approvals

**Activity Stats**:

- Today/This Week/This Month: Uploads, Queries, Approvals

**Most Active Users**:

- Top users by query count

**Recent Activity Feed**:

- Real-time activity stream

**Chat History Heatmap**:

- Visual calendar showing activity intensity

### Audit Logs

- View all system actions
- Filter by user, action type, date range
- Search by keyword
- Export to CSV

**Tracked Actions**:

- login, logout, upload_document, delete_document
- approve_user, reject_user, approve_document, reject_document
- role_changed, search_query, institution_created, data_source_requested

---

## 🎯 Additional Features

### Bookmarks

- Add/remove bookmarks
- View bookmarked documents
- Search/filter bookmarks

### Personal Notes

- Create notes with markdown support
- Link to documents
- Color coding, tagging
- Pin important notes
- Search notes

### Document Chat Rooms

- Real-time messaging per document
- Threading (reply to messages)
- Mentions (@username)
- Ask BEACON (AI responses)
- Active participants list
- Export chat to PDF

---

**Version**: 2.0.0  
**Status**: Production Ready  
**Last Updated**: December 4, 2025
