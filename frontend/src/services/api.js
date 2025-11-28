// import axios from "axios";

// const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// const api = axios.create({
//   baseURL: API_URL,
//   headers: { "Content-Type": "application/json" },
// });

// api.interceptors.request.use(
//   (config) => {
//     const token = localStorage.getItem("beacon-auth");
//     if (token) {
//       try {
//         const authData = JSON.parse(token);
//         if (authData?.state?.token) {
//           config.headers.Authorization = `Bearer ${authData.state.token}`;
//         }
//       } catch (error) {
//         console.error("Error parsing auth token:", error);
//       }
//     }
//     return config;
//   },
//   (error) => Promise.reject(error)
// );

// api.interceptors.response.use(
//   (response) => response,
//   (error) => {
//     if (error.response?.status === 401) {
//       localStorage.removeItem("beacon-auth");
//       window.location.href = "/login";
//     }
//     return Promise.reject(error);
//   }
// );

// export const authAPI = {
//   login: (credentials) => api.post("/api/auth/login", credentials),
//   register: (userData) => api.post("/api/auth/register", userData),
//   me: () => api.get("/api/auth/me"),
// };

// export const userAPI = {
//   listUsers: (params) => api.get("/api/users", { params }),
//   getUser: (userId) => api.get(`/api/users/${userId}`),
//   approveUser: (userId) => api.post(`/api/users/${userId}/approve`),
//   rejectUser: (userId) => api.post(`/api/users/${userId}/reject`),
//   changeRole: (userId, role) => api.put(`/api/users/${userId}/role`, { role }),
//   updateUser: (userId, data) => api.put(`/api/users/${userId}`, data),
// };

// export const documentAPI = {
//   listDocuments: (params) => api.get("/api/documents", { params }),
//   getDocument: (docId) => api.get(`/api/documents/${docId}`),
//   uploadDocument: (formData) =>
//     api.post("/api/documents/upload", formData, {
//       headers: { "Content-Type": "multipart/form-data" },
//     }),
//   approveDocument: (docId) => api.post(`/api/documents/${docId}/approve`),
//   rejectDocument: (docId) => api.post(`/api/documents/${docId}/reject`),
//   updateDocument: (docId, data) => api.put(`/api/documents/${docId}`, data),
//   deleteDocument: (docId) => api.delete(`/api/documents/${docId}`),
//   downloadDocument: (docId) =>
//     api.get(`/api/documents/${docId}/download`, { responseType: "blob" }),
//   reprocessEmbeddings: () => api.post("/api/documents/reprocess-embeddings"),
//   getVectorStats: () => api.get("/api/documents/vector-stats"),
// };

// export const institutionAPI = {
//   listInstitutions: () => api.get("/api/institutions"),
//   getInstitution: (instId) => api.get(`/api/institutions/${instId}`),
//   createInstitution: (data) => api.post("/api/institutions", data),
//   updateInstitution: (instId, data) =>
//     api.put(`/api/institutions/${instId}`, data),
//   deleteInstitution: (instId) => api.delete(`/api/institutions/${instId}`),
// };

// export const chatAPI = {
//   query: (question) => api.post("/api/chat/query", { question }),
// };

// export const systemAPI = {
//   health: () => api.get("/api/health"),
//   logs: (params) => api.get("/api/logs", { params }),
//   analytics: () => api.get("/api/analytics"),
// };

// export default api;
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
    if (error.response?.status === 401) {
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
};

// ============ USER ENDPOINTS ============
export const userAPI = {
  listUsers: (params) => api.get("/users/list", { params }),
  getPendingUsers: () => api.get("/users/pending"),
  approveUser: (userId, notes) => api.post(`/users/approve/${userId}`, { notes }),
  rejectUser: (userId, notes) => api.post(`/users/reject/${userId}`, { notes }),
  changeRole: (userId, newRole, notes) => api.patch(`/users/change-role/${userId}`, { new_role: newRole, notes }),
};

// ============ INSTITUTION ENDPOINTS ============
export const institutionAPI = {
  list: (type) => api.get("/institutions/list", { params: { type } }),
  create: (data) => api.post("/institutions/create", data),
  assignUser: (userId, institutionId) => api.patch(`/institutions/assign-user/${userId}`, { institution_id: institutionId }),
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
  updateMetadata: (docId, metadata) => api.patch(`/documents/${docId}/metadata`, metadata),
  deleteDocument: (docId) => api.delete(`/documents/${docId}`),
  downloadDocument: (docId) =>
    api.get(`/documents/${docId}/download`, { responseType: "blob" }),
  reprocessEmbeddings: () => api.post("/documents/reprocess-embeddings"),
  getVectorStats: () => api.get("/documents/vector-stats"),
};

// ============ APPROVAL ENDPOINTS ============
export const approvalAPI = {
  getPendingDocuments: () => api.get("/approvals/documents/pending"),
  approveDocument: (docId, notes) => api.post(`/approvals/documents/approve/${docId}`, { notes }),
  rejectDocument: (docId, notes) => api.post(`/approvals/documents/reject/${docId}`, { notes }),
  getDocumentHistory: (docId) => api.get(`/approvals/documents/history/${docId}`),
};

// ============ AUDIT ENDPOINTS ============
export const auditAPI = {
  getLogs: (params) => api.get("/audit/logs", { params }),
  getActionTypes: () => api.get("/audit/actions"),
  getUserActivity: (userId, days) => api.get(`/audit/user/${userId}/activity`, { params: { days } }),
  getSummary: (days) => api.get("/audit/summary", { params: { days } }),
};

// ============ CHAT ENDPOINTS ============
export const chatAPI = {
  query: (question, filters) => api.post("/chat/query", { question, filters }),
  getHistory: () => api.get("/chat/history"),
};

// ============ SYSTEM ENDPOINTS ============
export const systemAPI = {
  health: () => api.get("/health"),
  root: () => api.get("/"),
};

export default api;