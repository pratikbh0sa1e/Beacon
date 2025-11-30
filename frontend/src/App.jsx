import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useAuthStore } from "./stores/authStore";
import { PublicRoute } from "./middleware/PublicRoute";
import { ProtectedRoute } from "./middleware/ProtectedRoute";
import { MainLayout } from "./components/layout/MainLayout";
import { LoginPage } from "./pages/auth/LoginPage";
import { RegisterPage } from "./pages/auth/RegisterPage";
import { PendingApprovalPage } from "./pages/auth/PendingApprovalPage";
import { DashboardPage } from "./pages/DashboardPage";
import { DocumentExplorerPage } from "./pages/documents/DocumentExplorerPage";
import { DocumentDetailPage } from "./pages/documents/DocumentDetailPage";
import { DocumentUploadPage } from "./pages/documents/DocumentUploadPage";
import { AIChatPage } from "./pages/AIChatPage";
import { UserManagementPage } from "./pages/admin/UserManagementPage";
import { ADMIN_ROLES, DOCUMENT_MANAGER_ROLES } from "./constants/roles";
import { Toaster } from "./components/ui/sonner";
import { InstitutionsPage } from "./pages/admin/InstitutionsPage";
const App = () => {
  return (
    <BrowserRouter>
      <Toaster position="top-right" richColors />
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
          <Route path="documents" element={<DocumentExplorerPage />} />
          <Route path="documents/:id" element={<DocumentDetailPage />} />
          <Route
            path="upload"
            element={
              <ProtectedRoute allowedRoles={DOCUMENT_MANAGER_ROLES}>
                <DocumentUploadPage />
              </ProtectedRoute>
            }
          />
          <Route path="ai-chat" element={<AIChatPage />} />
          <Route
            path="admin/users"
            element={
              <ProtectedRoute allowedRoles={ADMIN_ROLES}>
                <UserManagementPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="admin/institutions"
            element={
              <ProtectedRoute allowedRoles={ADMIN_ROLES}>
                <InstitutionsPage />
              </ProtectedRoute>
            }
          />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
