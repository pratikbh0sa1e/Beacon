import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
});

// Request interceptor - add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("beacon-auth");
    if (token) {
      try {
        const authData = JSON.parse(token);
        if (authData?.state?.token) {
          config.headers.Authorization = `Bearer ${authData.state.token}`;
        }
      } catch (error) {
        console.error("Error parsing auth token:", error);
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // if (error.response?.status === 401) {
    //   localStorage.removeItem("beacon-auth");
    //   window.location.href = "/login";
    // }
    if (
      error.response?.status === 401 &&
      !error.config.url.includes("/auth/login")
    ) {
      localStorage.removeItem("beacon-auth");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// ============ AUTH ENDPOINTS ============
export const authAPI = {
  login: (credentials) => api.post("/auth/login", credentials),
  register: (userData) => api.post("/auth/register", userData),
  me: () => api.get("/auth/me"),
  logout: () => api.post("/auth/logout"),
  verifyEmail: (token) => api.get(`/auth/verify-email/${token}`),
  resendVerification: (email) =>
    api.post("/auth/resend-verification", null, { params: { email } }),
};

// ============ USER ENDPOINTS ============
export const userAPI = {
  listUsers: (params) => api.get("/users/list", { params }),
  getPendingUsers: () => api.get("/users/pending"),
  approveUser: (userId, notes) =>
    api.post(`/users/approve/${userId}`, { notes }),
  rejectUser: (userId, notes) => api.post(`/users/reject/${userId}`, { notes }),
  revokeApproval: (userId, notes) =>
    api.post(`/users/revoke/${userId}`, { notes }),
  deleteUser: (userId) => api.delete(`/users/delete/${userId}`),
  changeRole: (userId, newRole, notes) =>
    api.patch(`/users/change-role/${userId}`, { new_role: newRole, notes }),
};

// ============ INSTITUTION ENDPOINTS ============
export const institutionAPI = {
  list: (type) => api.get("/institutions/list", { params: { type } }),
  create: (data) => api.post("/institutions/create", data),
  assignUser: (userId, institutionId) =>
    api.patch(`/institutions/assign-user/${userId}`, {
      institution_id: institutionId,
    }),
  getUsers: (institutionId) => api.get(`/institutions/${institutionId}/users`),
};

// ============ DOCUMENT ENDPOINTS ============
export const documentAPI = {
  listDocuments: (params) => api.get("/documents/list", { params }),
  getDocument: (docId) => api.get(`/documents/${docId}`),
  uploadDocument: (formData) =>
    api.post("/documents/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  updateMetadata: (docId, metadata) =>
    api.patch(`/documents/${docId}/metadata`, metadata),
  deleteDocument: (docId) => api.delete(`/documents/${docId}`),
  downloadDocument: (docId) =>
    api.get(`/documents/${docId}/download`, { responseType: "blob" }),
  reprocessEmbeddings: () => api.post("/documents/reprocess-embeddings"),
  getVectorStats: () => api.get("/documents/vector-stats"),
};

// ============ APPROVAL ENDPOINTS ============
export const approvalAPI = {
  getPendingDocuments: () => api.get("/approvals/documents/pending"),
  getApprovedDocuments: () => api.get("/approvals/documents/approved"),
  getRejectedDocuments: () => api.get("/approvals/documents/rejected"),
  approveDocument: (docId, notes) =>
    api.post(`/approvals/documents/approve/${docId}`, { notes }),
  rejectDocument: (docId, notes) =>
    api.post(`/approvals/documents/reject/${docId}`, { notes }),
  getDocumentHistory: (docId) =>
    api.get(`/approvals/documents/history/${docId}`),
};

// ============ BOOKMARK ENDPOINTS (NEW) ============
export const bookmarkAPI = {
  toggle: (docId) => api.post(`/bookmark/toggle/${docId}`),
  list: () => api.get("/bookmark/list"),
};

// ============ NOTIFICATION ENDPOINTS ============
export const notificationAPI = {
  list: (params) => api.get("/notifications/list", { params }),
  grouped: () => api.get("/notifications/grouped"),
  unreadCount: () => api.get("/notifications/unread-count"),
  markRead: (id) => api.post(`/notifications/${id}/mark-read`),
  markAllRead: () => api.post("/notifications/mark-all-read"),
  delete: (id) => api.delete(`/notifications/${id}`),
  clearAll: () => api.delete("/notifications/clear-all"),
};

// ============ AUDIT ENDPOINTS ============
export const auditAPI = {
  getLogs: (params) => api.get("/audit/logs", { params }),
  getActionTypes: () => api.get("/audit/actions"),
  getUserActivity: (userId, days) =>
    api.get(`/audit/user/${userId}/activity`, { params: { days } }),
  getSummary: (days) => api.get("/audit/summary", { params: { days } }),
};

// ============ CHAT ENDPOINTS ============
export const chatAPI = {
  query: (question, filters) => api.post("/chat/query", { question, filters }),
  getHistory: () => api.get("/chat/history"),
};

// ============ VOICE ENDPOINTS ============
export const voiceAPI = {
  transcribe: (audioFile, language = null) => {
    const formData = new FormData();
    formData.append("audio", audioFile);
    if (language) formData.append("language", language);
    return api.post("/voice/transcribe", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  query: (audioFile, language = null, threadId = null) => {
    const formData = new FormData();
    formData.append("audio", audioFile);
    if (language) formData.append("language", language);
    if (threadId) formData.append("thread_id", threadId);
    return api.post("/voice/query", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  queryStream: (audioFile, language = null, threadId = null) => {
    const formData = new FormData();
    formData.append("audio", audioFile);
    if (language) formData.append("language", language);
    if (threadId) formData.append("thread_id", threadId);
    return `${API_URL}/voice/query/stream`;
  },
  engineInfo: () => api.get("/voice/engine-info"),
  health: () => api.get("/voice/health"),
};

// ============ SYSTEM ENDPOINTS ============
export const systemAPI = {
  health: () => api.get("/health"),
  root: () => api.get("/"),
};

export default api;
