// App.jsx

import { useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "sonner";
import { useAuthStore } from "./stores/authStore";
import { useThemeStore } from "./stores/themeStore";
import { PublicRoute } from "./middleware/PublicRoute";
import { ProtectedRoute } from "./middleware/ProtectedRoute";
import { MainLayout } from "./components/layout/MainLayout";
import { SessionWarningModal } from "./components/auth/SessionWarningModal";
import { ActivityTracker } from "./components/auth/ActivityTracker";

// Landing Page
import { LandingPage } from "./pages/LandingPage";

// Auth Pages
import { LoginPage } from "./pages/auth/LoginPage";
import { RegisterPage } from "./pages/auth/RegisterPage";
import { RegisterSuccessPage } from "./pages/auth/RegisterSuccessPage";
import { VerifyEmailPage } from "./pages/auth/VerifyEmailPage";
import { ResendVerificationPage } from "./pages/auth/ResendVerificationPage";
import { PendingApprovalPage } from "./pages/auth/PendingApprovalPage";

// Main Pages
import { DashboardPage } from "./pages/DashboardPage";

// Document Pages
import { DocumentExplorerPage } from "./pages/documents/DocumentExplorerPage";
import { DocumentDetailPage } from "./pages/documents/DocumentDetailPage";
import { DocumentUploadPage } from "./pages/documents/DocumentUploadPage";
import { ApprovalsPage } from "./pages/documents/ApprovalsPage";

// AI Chat
import { AIChatPage } from "./pages/AIChatPage";

// Admin Pages
import { UserManagementPage } from "./pages/admin/UserManagementPage";
import { InstitutionsPage } from "./pages/admin/InstitutionsPage";
import { AnalyticsPage } from "./pages/admin/AnalyticsPage";
import { SystemHealthPage } from "./pages/admin/SystemHealthPage";
import { DataSourceRequestPage } from "./pages/admin/DataSourceRequestPage";
import { DataSourceApprovalPage } from "./pages/admin/DataSourceApprovalPage";
import { ActiveSourcesPage } from "./pages/admin/ActiveSourcesPage";
import { MyDataSourceRequestsPage } from "./pages/admin/MyDataSourceRequestsPage";
import { WebScrapingPage } from "./pages/admin/WebScrapingPage";
import { EnhancedWebScrapingPage } from "./pages/admin/EnhancedWebScrapingPage";

// Bookmark Page
import { NotFoundPage } from "./pages/NotFoundPage";
import { BookmarksPage } from "./pages/BookmarksPage";

// Notes Page
import { NotesPage } from "./pages/NotesPage";

// OCR Page
import OCRReviewPage from "./pages/OCRReviewPage";

// User Pages
import { ProfilePage } from "./pages/ProfilePage";
import { SettingsPage } from "./pages/SettingsPage";

// Support Page
import { SupportPage } from "./pages/SupportPage";

// Constants
import { ADMIN_ROLES, DOCUMENT_MANAGER_ROLES } from "./constants/roles";

// Root Route Component - Conditional rendering based on auth state
const RootRoute = () => {
  const { isAuthenticated, user } = useAuthStore();

  // If not authenticated, show landing page
  if (!isAuthenticated) {
    return <LandingPage />;
  }

  // If authenticated but not approved, redirect to pending approval
  if (user && !user.approved) {
    return <Navigate to="/pending-approval" replace />;
  }

  // If authenticated and approved, show dashboard layout
  return (
    <ProtectedRoute>
      <MainLayout />
    </ProtectedRoute>
  );
};

const App = () => {
  const initTheme = useThemeStore((state) => state.initTheme);
  const initAuth = useAuthStore((state) => state.initAuth);
  const theme = useThemeStore((state) => state.theme);

  useEffect(() => {
    initTheme();
    initAuth();
  }, [initTheme, initAuth]);

  return (
    <BrowserRouter>
      <ActivityTracker />
      <SessionWarningModal />
      <Toaster position="top-right" richColors closeButton theme={theme} />

      <Routes>
        <Route
          path="/login"
          element={
            <PublicRoute>
              <LoginPage />
            </PublicRoute>
          }
        />

        <Route
          path="/register"
          element={
            <PublicRoute>
              <RegisterPage />
            </PublicRoute>
          }
        />

        <Route
          path="/register-success"
          element={
            <PublicRoute>
              <RegisterSuccessPage />
            </PublicRoute>
          }
        />

        <Route
          path="/verify-email"
          element={
            <PublicRoute>
              <VerifyEmailPage />
            </PublicRoute>
          }
        />

        <Route
          path="/resend-verification"
          element={
            <PublicRoute>
              <ResendVerificationPage />
            </PublicRoute>
          }
        />

        <Route
          path="/pending-approval"
          element={
            <ProtectedRoute requireApproval={false}>
              <PendingApprovalPage />
            </ProtectedRoute>
          }
        />

        {/* Root Route - Conditional: Landing Page or Dashboard */}
        <Route path="/" element={<RootRoute />}>
          {/* These routes only render when authenticated */}
          <Route index element={<DashboardPage />} />

          <Route path="documents">
            <Route index element={<DocumentExplorerPage />} />
            <Route path=":id" element={<DocumentDetailPage />} />
          </Route>
          <Route path="bookmarks" element={<BookmarksPage />} />
          <Route path="notes" element={<NotesPage />} />
          <Route
            path="approvals"
            element={
              <ProtectedRoute
                allowedRoles={[
                  "developer",
                  "ministry_admin",
                  "university_admin",
                ]}
              >
                <ApprovalsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="ocr-review"
            element={
              <ProtectedRoute
                allowedRoles={[
                  "developer",
                  "ministry_admin",
                  "university_admin",
                  "document_officer",
                ]}
              >
                <OCRReviewPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="upload"
            element={
              <ProtectedRoute allowedRoles={DOCUMENT_MANAGER_ROLES}>
                <DocumentUploadPage />
              </ProtectedRoute>
            }
          />

          <Route path="ai-chat" element={<AIChatPage />} />

          <Route path="profile" element={<ProfilePage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="support" element={<SupportPage />} />

          <Route path="admin">
            <Route
              path="users"
              element={
                <ProtectedRoute allowedRoles={ADMIN_ROLES}>
                  <UserManagementPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="institutions"
              element={
                <ProtectedRoute allowedRoles={ADMIN_ROLES}>
                  <InstitutionsPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="data-sources"
              element={
                <ProtectedRoute
                  allowedRoles={["ministry_admin", "university_admin"]}
                >
                  <DataSourceRequestPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="my-data-source-requests"
              element={
                <ProtectedRoute
                  allowedRoles={[
                    "ministry_admin",
                    "university_admin",
                    "developer",
                  ]}
                >
                  <MyDataSourceRequestsPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="data-source-approvals"
              element={
                <ProtectedRoute allowedRoles={["developer"]}>
                  <DataSourceApprovalPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="web-scraping"
              element={
                <ProtectedRoute allowedRoles={ADMIN_ROLES}>
                  <WebScrapingPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="web-scraping-enhanced"
              element={
                <ProtectedRoute allowedRoles={ADMIN_ROLES}>
                  <EnhancedWebScrapingPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="active-sources"
              element={
                <ProtectedRoute allowedRoles={["developer"]}>
                  <ActiveSourcesPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="analytics"
              element={
                <ProtectedRoute allowedRoles={ADMIN_ROLES}>
                  <AnalyticsPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="system"
              element={
                <ProtectedRoute allowedRoles={["developer"]}>
                  <SystemHealthPage />
                </ProtectedRoute>
              }
            />

            <Route index element={<Navigate to="/admin/users" replace />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>

        {/* 404 - Catch all unmatched routes */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
