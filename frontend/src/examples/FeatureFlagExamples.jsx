/**
 * BEACON - Feature Flag Usage Examples
 *
 * This file shows how to use feature flags in different components
 * Copy these patterns to your actual components
 */

import React from "react";
import FeatureFlag from "../components/FeatureFlag";
import {
  isFeatureEnabled,
  features,
  currentRound,
  currentRoundInfo,
} from "../config/featureFlags";

// ============================================
// EXAMPLE 1: Conditional Component Rendering
// ============================================

const Sidebar = () => {
  return (
    <div className="sidebar">
      {/* Always visible */}
      <SidebarItem icon="home" label="Dashboard" to="/" />
      <SidebarItem icon="file" label="Documents" to="/documents" />
      <SidebarItem icon="chat" label="AI Chat" to="/chat" />

      {/* Round 2+ only */}
      <FeatureFlag feature="BOOKMARKS">
        <SidebarItem icon="bookmark" label="Bookmarks" to="/bookmarks" />
      </FeatureFlag>

      <FeatureFlag feature="NOTES">
        <SidebarItem icon="note" label="Notes" to="/notes" />
      </FeatureFlag>

      {/* Round 3 only */}
      <FeatureFlag feature="ANALYTICS">
        <SidebarItem icon="chart" label="Analytics" to="/analytics" />
      </FeatureFlag>

      <FeatureFlag feature="SYSTEM_HEALTH">
        <SidebarItem icon="health" label="System Health" to="/system-health" />
      </FeatureFlag>
    </div>
  );
};

// ============================================
// EXAMPLE 2: Conditional Button in Header
// ============================================

const Header = () => {
  return (
    <header className="header">
      <Logo />
      <SearchBar />

      {/* Voice button only in Round 2+ */}
      <FeatureFlag feature="VOICE_QUERY">
        <button className="voice-btn">
          <MicIcon /> Voice Search
        </button>
      </FeatureFlag>

      {/* Notifications only in Round 2+ */}
      <FeatureFlag feature="NOTIFICATIONS">
        <NotificationBell />
      </FeatureFlag>

      <UserMenu />
    </header>
  );
};

// ============================================
// EXAMPLE 3: Conditional Page Routes
// ============================================

import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

const AppRoutes = () => {
  return (
    <Routes>
      {/* Always available */}
      <Route path="/" element={<DashboardPage />} />
      <Route path="/documents" element={<DocumentExplorerPage />} />
      <Route path="/chat" element={<AIChatPage />} />

      {/* Round 2+ routes */}
      {isFeatureEnabled("BOOKMARKS") && (
        <Route path="/bookmarks" element={<BookmarksPage />} />
      )}

      {isFeatureEnabled("NOTES") && (
        <Route path="/notes" element={<NotesPage />} />
      )}

      {isFeatureEnabled("APPROVAL_WORKFLOW") && (
        <Route path="/admin/approvals" element={<DocumentApprovalsPage />} />
      )}

      {/* Round 3 routes */}
      {isFeatureEnabled("ANALYTICS") && (
        <Route path="/admin/analytics" element={<AnalyticsPage />} />
      )}

      {isFeatureEnabled("EXTERNAL_DATA_SYNC") && (
        <Route path="/admin/data-sources" element={<DataSourcesPage />} />
      )}

      {isFeatureEnabled("SYSTEM_HEALTH") && (
        <Route path="/admin/system-health" element={<SystemHealthPage />} />
      )}

      {/* Redirect disabled routes to home */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

// ============================================
// EXAMPLE 4: Conditional Features in Document Card
// ============================================

const DocumentCard = ({ document }) => {
  return (
    <div className="document-card">
      <h3>{document.title}</h3>
      <p>{document.description}</p>

      <div className="actions">
        {/* Always available */}
        <button>View</button>
        <button>Download</button>

        {/* Round 2+ features */}
        <FeatureFlag feature="BOOKMARKS">
          <button>Bookmark</button>
        </FeatureFlag>

        <FeatureFlag feature="NOTES">
          <button>Add Note</button>
        </FeatureFlag>

        {/* Round 3 features */}
        <FeatureFlag feature="DOCUMENT_CHAT">
          <button>Join Chat</button>
        </FeatureFlag>
      </div>

      {/* Show approval status only in Round 2+ */}
      <FeatureFlag feature="APPROVAL_WORKFLOW">
        <div className="approval-status">
          Status: {document.approval_status}
        </div>
      </FeatureFlag>
    </div>
  );
};

// ============================================
// EXAMPLE 5: Conditional Admin Menu
// ============================================

const AdminMenu = ({ userRole }) => {
  // Only show admin menu for admin roles
  if (!["developer", "ministry_admin", "university_admin"].includes(userRole)) {
    return null;
  }

  return (
    <div className="admin-menu">
      <h3>Admin Panel</h3>

      {/* Always available */}
      <MenuItem to="/admin/users">User Management</MenuItem>

      {/* Round 2+ features */}
      <FeatureFlag feature="APPROVAL_WORKFLOW">
        <MenuItem to="/admin/approvals">Document Approvals</MenuItem>
        <MenuItem to="/admin/user-approvals">User Approvals</MenuItem>
      </FeatureFlag>

      <FeatureFlag feature="INSTITUTION_MANAGEMENT">
        <MenuItem to="/admin/institutions">Institutions</MenuItem>
      </FeatureFlag>

      {/* Round 3 features */}
      <FeatureFlag feature="ANALYTICS">
        <MenuItem to="/admin/analytics">Analytics</MenuItem>
      </FeatureFlag>

      <FeatureFlag feature="EXTERNAL_DATA_SYNC">
        <MenuItem to="/admin/data-sources">External Data Sources</MenuItem>
      </FeatureFlag>

      <FeatureFlag feature="SYSTEM_HEALTH">
        <MenuItem to="/admin/system-health">System Health</MenuItem>
      </FeatureFlag>
    </div>
  );
};

// ============================================
// EXAMPLE 6: Conditional API Calls
// ============================================

const DocumentUploadPage = () => {
  const handleUpload = async (file, metadata) => {
    // Upload document (always available)
    const response = await uploadDocument(file, metadata);

    // Extract metadata only in Round 2+
    if (isFeatureEnabled("METADATA_EXTRACTION")) {
      await extractMetadata(response.document_id);
    }

    // Trigger approval workflow only in Round 2+
    if (isFeatureEnabled("APPROVAL_WORKFLOW")) {
      await submitForApproval(response.document_id);
    }

    return response;
  };

  return (
    <div>
      <h1>Upload Document</h1>
      <FileUploader onUpload={handleUpload} />

      {/* Show approval notice in Round 2+ */}
      <FeatureFlag feature="APPROVAL_WORKFLOW">
        <div className="notice">
          Your document will be submitted for approval after upload.
        </div>
      </FeatureFlag>
    </div>
  );
};

// ============================================
// EXAMPLE 7: Conditional Form Fields
// ============================================

const DocumentUploadForm = () => {
  return (
    <form>
      {/* Always required */}
      <input name="title" placeholder="Title" required />
      <textarea name="description" placeholder="Description" />
      <select name="visibility">
        <option value="public">Public</option>
        <option value="institution">Institution Only</option>
      </select>

      {/* Round 2+ fields */}
      <FeatureFlag feature="METADATA_EXTRACTION">
        <div className="info">
          Metadata will be automatically extracted after upload
        </div>
      </FeatureFlag>

      {/* Round 3 fields */}
      <FeatureFlag feature="DOCUMENT_EXPIRY">
        <input type="date" name="expiry_date" placeholder="Expiry Date" />
      </FeatureFlag>

      <FeatureFlag feature="DOWNLOAD_RESTRICTIONS">
        <label>
          <input type="checkbox" name="download_allowed" />
          Allow downloads
        </label>
      </FeatureFlag>

      <button type="submit">Upload</button>
    </form>
  );
};

// ============================================
// EXAMPLE 8: Conditional Dashboard Widgets
// ============================================

const DashboardPage = () => {
  return (
    <div className="dashboard">
      <h1>Dashboard</h1>

      {/* Always visible */}
      <StatsCard title="Total Documents" value={120} />
      <RecentDocuments />

      {/* Round 2+ widgets */}
      <FeatureFlag feature="APPROVAL_WORKFLOW">
        <PendingApprovalsWidget />
      </FeatureFlag>

      <FeatureFlag feature="NOTIFICATIONS">
        <RecentNotificationsWidget />
      </FeatureFlag>

      {/* Round 3 widgets */}
      <FeatureFlag feature="ANALYTICS">
        <ActivityChartWidget />
        <PopularDocumentsWidget />
      </FeatureFlag>

      <FeatureFlag feature="SYSTEM_HEALTH">
        <SystemHealthWidget />
      </FeatureFlag>
    </div>
  );
};

// ============================================
// EXAMPLE 9: Using isFeatureEnabled in Logic
// ============================================

const ChatPage = () => {
  const [query, setQuery] = useState("");
  const [useVoice, setUseVoice] = useState(false);

  const handleSubmit = async () => {
    let finalQuery = query;

    // Use voice input if enabled and selected
    if (isFeatureEnabled("VOICE_QUERY") && useVoice) {
      finalQuery = await transcribeVoice();
    }

    // Send query to RAG
    const response = await askAI(finalQuery);

    // Save to bookmarks if enabled
    if (isFeatureEnabled("BOOKMARKS")) {
      showBookmarkOption(response);
    }

    return response;
  };

  return (
    <div>
      <textarea value={query} onChange={(e) => setQuery(e.target.value)} />

      {/* Show voice toggle only if enabled */}
      {isFeatureEnabled("VOICE_QUERY") && (
        <label>
          <input
            type="checkbox"
            checked={useVoice}
            onChange={(e) => setUseVoice(e.target.checked)}
          />
          Use voice input
        </label>
      )}

      <button onClick={handleSubmit}>Ask AI</button>
    </div>
  );
};

// ============================================
// EXAMPLE 10: Round Info Display (for demos)
// ============================================

const RoundBadge = () => {
  // Only show in development mode
  if (import.meta.env.PROD) return null;

  return (
    <div className="fixed top-4 right-4 bg-blue-500 text-white px-4 py-2 rounded-lg shadow-lg">
      <div className="font-bold">{currentRoundInfo.name}</div>
      <div className="text-sm">{currentRoundInfo.description}</div>
      <div className="text-xs mt-1">
        Implementation: {currentRoundInfo.percentage}
      </div>
    </div>
  );
};

// Add to your App.jsx:
// <RoundBadge />

export {
  Sidebar,
  Header,
  AppRoutes,
  DocumentCard,
  AdminMenu,
  DocumentUploadPage,
  DocumentUploadForm,
  DashboardPage,
  ChatPage,
  RoundBadge,
};
