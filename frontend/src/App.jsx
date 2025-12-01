// App.jsx

import React, { useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "sonner";
import { useAuthStore } from "./stores/authStore";
import { useThemeStore } from "./stores/themeStore";
import { PublicRoute } from "./middleware/PublicRoute";
import { ProtectedRoute } from "./middleware/ProtectedRoute";
import { MainLayout } from "./components/layout/MainLayout";
import { SessionWarningModal } from "./components/auth/SessionWarningModal";
import { ActivityTracker } from "./components/auth/ActivityTracker";

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

// AI Chat
import { AIChatPage } from "./pages/AIChatPage";

// Admin Pages
import { UserManagementPage } from "./pages/admin/UserManagementPage";
import { InstitutionsPage } from "./pages/admin/InstitutionsPage";
import { DocumentApprovalsPage } from "./pages/admin/DocumentApprovalsPage";
import { AnalyticsPage } from "./pages/admin/AnalyticsPage";
import { SystemHealthPage } from "./pages/admin/SystemHealthPage";

// Bookmark Page
import { NotFoundPage } from "./pages/NotFoundPage";
import { BookmarksPage } from "./pages/BookmarksPage";

// User Pages
import { ProfilePage } from "./pages/ProfilePage";
import { SettingsPage } from "./pages/SettingsPage";

// Constants
import { ADMIN_ROLES, DOCUMENT_MANAGER_ROLES } from "./constants/roles";

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

        <Route
          path="/"
          element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<DashboardPage />} />

          <Route path="documents">
            <Route index element={<DocumentExplorerPage />} />
            <Route path=":id" element={<DocumentDetailPage />} />
          </Route>
          <Route path="bookmarks" element={<BookmarksPage />} />
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
              path="approvals"
              element={
                <ProtectedRoute allowedRoles={ADMIN_ROLES}>
                  <DocumentApprovalsPage />
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
