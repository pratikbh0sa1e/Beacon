import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../services/api";
import { useAuthStore } from "../../stores/authStore";
import { toast } from "sonner";
import {
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
  FileText,
  Eye,
  Calendar,
  Building2,
  User,
} from "lucide-react";

export const ApprovalsPage = () => {
  const [allDocuments, setAllDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("pending");
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [showActionModal, setShowActionModal] = useState(false);
  const [modalAction, setModalAction] = useState("");
  const [reason, setReason] = useState("");
  const [processing, setProcessing] = useState(false);

  const { user } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    fetchAllDocuments();
  }, []);

  const fetchAllDocuments = async () => {
    try {
      setLoading(true);
      const response = await api.get("/documents/list", {
        params: { limit: 1000 },
      });
      setAllDocuments(response.data.documents || []);
    } catch (error) {
      console.error("Error fetching documents:", error);
      toast.error("Failed to load documents");
    } finally {
      setLoading(false);
    }
  };

  const filteredDocuments = allDocuments.filter((doc) => {
    if (activeTab === "pending") {
      return (
        doc.approval_status === "pending" ||
        doc.approval_status === "under_review"
      );
    } else if (activeTab === "approved") {
      return doc.approval_status === "approved";
    } else if (activeTab === "rejected") {
      return (
        doc.approval_status === "rejected" ||
        doc.approval_status === "changes_requested"
      );
    }
    return false;
  });

  const handleAction = (doc, action) => {
    setSelectedDoc(doc);
    setModalAction(action);
    setShowActionModal(true);
    setReason("");
  };

  const confirmAction = async () => {
    if (!selectedDoc) return;

    setProcessing(true);
    try {
      if (modalAction === "approve") {
        await api.post(`/documents/${selectedDoc.id}/approve`);
        toast.success("Document approved successfully");
      } else if (modalAction === "reject") {
        if (!reason.trim()) {
          toast.error("Please provide a reason for rejection");
          setProcessing(false);
          return;
        }
        await api.post(`/documents/${selectedDoc.id}/reject`, { reason });
        toast.success("Document rejected");
      } else if (modalAction === "changes") {
        if (!reason.trim()) {
          toast.error("Please specify what changes are needed");
          setProcessing(false);
          return;
        }
        await api.post(`/documents/${selectedDoc.id}/request-changes`, {
          changes_requested: reason,
        });
        toast.success("Changes requested successfully");
      }

      await fetchAllDocuments();
      setShowActionModal(false);
      setSelectedDoc(null);
    } catch (error) {
      console.error("Error processing action:", error);
      toast.error(error.response?.data?.detail || "Failed to process action");
    } finally {
      setProcessing(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const getStatusBadge = (status) => {
    const badges = {
      pending: {
        color:
          "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
        icon: Clock,
      },
      under_review: {
        color: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
        icon: Eye,
      },
      approved: {
        color:
          "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
        icon: CheckCircle,
      },
      rejected: {
        color: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
        icon: XCircle,
      },
      changes_requested: {
        color:
          "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200",
        icon: AlertCircle,
      },
    };

    const badge = badges[status] || badges.pending;
    const Icon = badge.icon;

    return (
      <span
        className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${badge.color}`}
      >
        <Icon className="w-3 h-3" />
        {status?.replace("_", " ").toUpperCase()}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <Clock className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">
            Loading documents...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Document Approvals
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Review and manage document approval requests
          </p>
        </div>

        <div className="mb-6 border-b border-gray-200 dark:border-gray-700">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveTab("pending")}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === "pending"
                  ? "border-blue-500 text-blue-600 dark:text-blue-400"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300"
              }`}
            >
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4" />
                Pending
                <span className="bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200 px-2 py-0.5 rounded-full text-xs">
                  {
                    allDocuments.filter(
                      (d) =>
                        d.approval_status === "pending" ||
                        d.approval_status === "under_review"
                    ).length
                  }
                </span>
              </div>
            </button>

            <button
              onClick={() => setActiveTab("approved")}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === "approved"
                  ? "border-green-500 text-green-600 dark:text-green-400"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300"
              }`}
            >
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4" />
                Approved
                <span className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 px-2 py-0.5 rounded-full text-xs">
                  {
                    allDocuments.filter((d) => d.approval_status === "approved")
                      .length
                  }
                </span>
              </div>
            </button>

            <button
              onClick={() => setActiveTab("rejected")}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === "rejected"
                  ? "border-red-500 text-red-600 dark:text-red-400"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300"
              }`}
            >
              <div className="flex items-center gap-2">
                <XCircle className="w-4 h-4" />
                Rejected
                <span className="bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 px-2 py-0.5 rounded-full text-xs">
                  {
                    allDocuments.filter(
                      (d) =>
                        d.approval_status === "rejected" ||
                        d.approval_status === "changes_requested"
                    ).length
                  }
                </span>
              </div>
            </button>
          </nav>
        </div>

        {filteredDocuments.length === 0 ? (
          <div className="bg-white dark:bg-gray-800 rounded-lg p-12 text-center shadow">
            <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              No {activeTab} documents
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              {activeTab === "pending" &&
                "No documents are waiting for approval."}
              {activeTab === "approved" &&
                "No documents have been approved yet."}
              {activeTab === "rejected" && "No documents have been rejected."}
            </p>
          </div>
        ) : (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-900">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Document
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Institution
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Uploader
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {filteredDocuments.map((doc) => (
                  <tr
                    key={doc.id}
                    className="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors cursor-pointer"
                    onClick={() => navigate(`/documents/${doc.id}`)}
                  >
                    <td className="px-6 py-4">
                      <div className="flex items-center">
                        <FileText className="w-5 h-5 text-gray-400 mr-3" />
                        <div>
                          <div className="text-sm font-medium text-gray-900 dark:text-white">
                            {doc.title}
                          </div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            {doc.category}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center text-sm text-gray-900 dark:text-white">
                        <Building2 className="w-4 h-4 mr-2 text-gray-400" />
                        {doc.institution_id || "N/A"}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center text-sm text-gray-900 dark:text-white">
                        <User className="w-4 h-4 mr-2 text-gray-400" />
                        {doc.uploader?.name || "Unknown"}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                        <Calendar className="w-4 h-4 mr-2" />
                        {formatDate(doc.created_at)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getStatusBadge(doc.approval_status)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div
                        className="flex items-center justify-end gap-2"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <button
                          onClick={() => navigate(`/documents/${doc.id}`)}
                          className="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300 flex items-center gap-1"
                        >
                          <Eye className="w-4 h-4" />
                          View
                        </button>

                        {activeTab === "pending" && (
                          <>
                            <button
                              onClick={() => handleAction(doc, "approve")}
                              className="text-green-600 hover:text-green-900 dark:text-green-400 dark:hover:text-green-300 flex items-center gap-1 ml-3"
                            >
                              <CheckCircle className="w-4 h-4" />
                              Approve
                            </button>
                            <button
                              onClick={() => handleAction(doc, "reject")}
                              className="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300 flex items-center gap-1 ml-3"
                            >
                              <XCircle className="w-4 h-4" />
                              Reject
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showActionModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg max-w-md w-full p-6">
            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
              {modalAction === "approve" && "Approve Document"}
              {modalAction === "reject" && "Reject Document"}
              {modalAction === "changes" && "Request Changes"}
            </h3>

            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Document: <strong>{selectedDoc?.title}</strong>
            </p>

            {(modalAction === "reject" || modalAction === "changes") && (
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {modalAction === "reject"
                    ? "Reason for rejection"
                    : "Changes needed"}
                </label>
                <textarea
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows="4"
                  placeholder={
                    modalAction === "reject"
                      ? "Explain why this document is being rejected..."
                      : "Describe what changes are needed..."
                  }
                />
              </div>
            )}

            {modalAction === "approve" && (
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                Are you sure you want to approve this document? It will become
                visible according to its visibility settings.
              </p>
            )}

            <div className="flex gap-3">
              <button
                onClick={confirmAction}
                disabled={processing}
                className={`flex-1 px-4 py-2 rounded-lg text-white transition-colors ${
                  modalAction === "approve"
                    ? "bg-green-600 hover:bg-green-700"
                    : modalAction === "reject"
                    ? "bg-red-600 hover:bg-red-700"
                    : "bg-yellow-600 hover:bg-yellow-700"
                } disabled:opacity-50`}
              >
                {processing ? "Processing..." : "Confirm"}
              </button>

              <button
                onClick={() => setShowActionModal(false)}
                disabled={processing}
                className="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded-lg transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
