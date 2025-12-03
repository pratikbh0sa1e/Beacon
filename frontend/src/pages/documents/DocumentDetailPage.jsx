import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Download,
  Eye,
  FileText,
  Calendar,
  Building2,
  Shield,
  Star,
  Send,
  AlertCircle,
  CheckCircle,
  MessageSquare,
} from "lucide-react";
import { documentAPI, bookmarkAPI } from "../../services/api";
import { LoadingSpinner } from "../../components/common/LoadingSpinner";
import { Button } from "../../components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { Separator } from "../../components/ui/separator";
import { formatDateTime } from "../../utils/dateFormat";
import { toast } from "sonner";
import { useAuthStore } from "../../stores/authStore";
import { SecureDocumentViewer } from "../../components/documents/SecureDocumentViewer";
import { DocumentChatPanel } from "../../components/documents/DocumentChatPanel";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../components/ui/tabs";

export const DocumentDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuthStore();
  // const [document, setDocument] = useState(null);
  const [docData, setDocData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (id) {
      fetchDocument();
      checkBookmarkStatus();
    }
  }, [id]);

  const fetchDocument = async () => {
    try {
      const response = await documentAPI.getDocument(id);
      // setDocument(response.data);
      setDocData(response.data);
    } catch (error) {
      console.error("Error fetching document:", error);
      toast.error("Failed to load document");
    } finally {
      setLoading(false);
    }
  };

  // ✅ Check if this doc is in user's bookmarks
  const checkBookmarkStatus = async () => {
    try {
      const response = await bookmarkAPI.list();
      const bookmarkedIds = response.data; // Array of IDs
      setIsBookmarked(bookmarkedIds.includes(parseInt(id)));
    } catch (error) {
      console.error("Error checking bookmark:", error);
    }
  };

  // ✅ Handle Bookmark Toggle
  const toggleBookmark = async () => {
    try {
      const response = await bookmarkAPI.toggle(id);
      setIsBookmarked(response.data.status === "added");
      toast.success(response.data.message);
    } catch (error) {
      toast.error("Failed to update bookmark");
    }
  };

  const handleDownload = async () => {
    try {
      const response = await documentAPI.downloadDocument(id);

      // Extract filename from Content-Disposition header if available
      const contentDisposition = response.headers["content-disposition"];
      let filename = docData.title;

      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      // response.data is already a Blob, don't wrap it again
      const url = window.URL.createObjectURL(response.data);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url); // Clean up
      toast.success("Document downloaded successfully");
    } catch (error) {
      console.error("Download error:", error);
      toast.error("Failed to download document");
    }
  };

  const handleSubmitForReview = async () => {
    setSubmitting(true);
    try {
      await documentAPI.submitForReview(id);
      toast.success(
        "Document submitted for MoE review successfully! MoE administrators have been notified."
      );
      fetchDocument(); // Refresh to show updated status
    } catch (error) {
      console.error("Submit error:", error);
      toast.error(error.response?.data?.detail || "Failed to submit document");
    } finally {
      setSubmitting(false);
    }
  };

  const handlePublish = async () => {
    setSubmitting(true);
    try {
      await documentAPI.approveDocument(id);
      toast.success("Document published successfully!");
      fetchDocument(); // Refresh to show updated status
    } catch (error) {
      console.error("Publish error:", error);
      toast.error(error.response?.data?.detail || "Failed to publish document");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <LoadingSpinner text="Loading document..." />;
  }

  if (!docData) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Document not found</p>
        <Button onClick={() => navigate("/documents")} className="mt-4">
          Back to Documents
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center gap-4">
        <Button
          variant="outline"
          size="icon"
          onClick={() => navigate("/documents")}
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1">
          {/* <h1 className="text-3xl font-bold">{document.title}</h1> */}
          <h1 className="text-3xl font-bold">{docData.title}</h1>
          <div className="flex items-center gap-2 mt-2">
            <Badge>{docData.category}</Badge>
            <Badge variant="outline">{docData.visibility}</Badge>
            {/* Status Badge */}
            <Badge
              className={
                docData.approval_status === "approved"
                  ? "bg-green-600"
                  : docData.approval_status === "pending"
                    ? "bg-yellow-600"
                    : docData.approval_status === "rejected"
                      ? "bg-red-600"
                      : docData.approval_status === "draft"
                        ? "bg-gray-600"
                        : "bg-blue-600"
              }
            >
              {docData.approval_status?.replace("_", " ").toUpperCase()}
            </Badge>
          </div>
        </div>

        {/* ✅ Bookmark Button */}
        <Button
          variant="outline"
          size="icon"
          onClick={toggleBookmark}
          className={
            isBookmarked
              ? "text-yellow-500 border-yellow-500/50 bg-yellow-500/10"
              : "text-muted-foreground"
          }
        >
          <Star className={`h-5 w-5 ${isBookmarked ? "fill-current" : ""}`} />
        </Button>

        {/* ✅ Publish Button for MoE Admin - Direct publish without approval */}
        {(user?.role === "moe_admin" || user?.role === "developer") &&
          docData.approval_status === "draft" && (
            <Button
              onClick={handlePublish}
              disabled={submitting}
              className="bg-green-600 hover:bg-green-700"
            >
              <CheckCircle className="h-4 w-4 mr-2" />
              {submitting ? "Publishing..." : "Publish Document"}
            </Button>
          )}

        {/* ✅ Submit for Review Button - Only for University users (NOT MoE) */}
        {/* MoE Admin and Developer don't need approval - their uploads are auto-approved */}
        {user?.role !== "moe_admin" &&
          user?.role !== "developer" &&
          ((user?.role === "university_admin" &&
            user?.institution_id === docData.institution_id) ||
            user?.id === docData.uploader?.id) &&
          docData.approval_status !== "pending" &&
          docData.approval_status !== "approved" &&
          docData.approval_status !== "under_review" && (
            <Button
              onClick={handleSubmitForReview}
              disabled={submitting}
              className="bg-blue-600 hover:bg-blue-700"
            >
              <Send className="h-4 w-4 mr-2" />
              {submitting ? "Submitting..." : "Submit for MoE Review"}
            </Button>
          )}

        {/* ✅ Show Download Button only if allowed */}
        {docData.download_allowed && (
          <Button onClick={handleDownload} className="neon-glow">
            <Download className="h-4 w-4 mr-2" />
            Download
          </Button>
        )}
      </div>

      <Card className="glass-card border-border/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Document Information
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* ⚠️ Rejection/Changes Requested Notice */}
          {(docData.approval_status === "rejected" ||
            docData.approval_status === "changes_requested") &&
            docData.rejection_reason && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-red-900 dark:text-red-100 mb-1">
                      {docData.approval_status === "rejected"
                        ? "Document Rejected"
                        : "Changes Requested"}
                    </h4>
                    <p className="text-sm text-red-800 dark:text-red-200">
                      {docData.rejection_reason}
                    </p>
                  </div>
                </div>
              </div>
            )}

          {/* ✅ NEW: Smart Description with AI Badge */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold">Description</h3>

              {/* Show badge ONLY if we are falling back to AI text */}
              {!docData.user_description && docData.ai_summary && (
                <Badge
                  variant="secondary"
                  className="text-xs bg-primary/10 text-primary hover:bg-primary/20 border-primary/20"
                >
                  ✨ AI Generated
                </Badge>
              )}
            </div>

            <div className="bg-muted/30 p-4 rounded-lg border border-border/50">
              <p className="text-muted-foreground leading-relaxed whitespace-pre-wrap">
                {/* Priority: User Text -> AI Text -> Fallback Message */}
                {docData.description ||
                  "No description available yet (AI processing...)"}
              </p>
            </div>
          </div>

          <Separator />

          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <Building2 className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">Department</p>
                  <p className="font-medium">{docData.department}</p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <Calendar className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">Year</p>
                  <p className="font-medium">{docData.year || "N/A"}</p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <FileText className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">Version</p>
                  <p className="font-medium">{docData.version || "1.0"}</p>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <Shield className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">Visibility</p>
                  <p className="font-medium capitalize">{docData.visibility}</p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <Eye className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">
                    Download Allowed
                  </p>
                  <p className="font-medium">
                    {docData.download_allowed ? "Yes" : "No"}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <Calendar className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">Last Updated</p>
                  <p className="font-medium">
                    {formatDateTime(docData.updated_at)}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* ✅ Show Institution only if it exists */}
          {docData.institution && (
            <>
              <Separator />
              <div>
                <p className="text-sm text-muted-foreground mb-1">
                  Institution
                </p>
                <p className="font-medium">{docData.institution.name}</p>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Preview & Chat Tabs */}
      <Card className="glass-card border-border/50">
        <CardContent className="p-0">
          <Tabs defaultValue="preview" className="w-full">
            <div className="border-b border-border/50 px-6 pt-6">
              <TabsList className="grid w-full max-w-md grid-cols-2">
                <TabsTrigger value="preview" className="flex items-center gap-2">
                  <Eye className="h-4 w-4" />
                  Preview
                </TabsTrigger>
                <TabsTrigger value="chat" className="flex items-center gap-2">
                  <MessageSquare className="h-4 w-4" />
                  Discussion
                </TabsTrigger>
              </TabsList>
            </div>

            <TabsContent value="preview" className="p-6 m-0">
              <div className="flex items-center gap-2 mb-4">
                <h3 className="font-semibold">Document Preview</h3>
                {docData.download_allowed ? (
                  <Badge
                    variant="secondary"
                    className="text-xs bg-green-500/10 text-green-600 border-green-500/20"
                  >
                    ✓ Preview Available
                  </Badge>
                ) : (
                  <Badge
                    variant="secondary"
                    className="text-xs bg-red-500/10 text-red-600 border-red-500/20"
                  >
                    🔒 Protected
                  </Badge>
                )}
              </div>

              {!docData.download_allowed ? (
                <div className="aspect-[4/3] bg-muted/50 rounded-lg flex items-center justify-center border border-border/50">
                  <div className="text-center p-6 max-w-md">
                    <Shield className="h-16 w-16 mx-auto mb-4 text-muted-foreground/50" />
                    <p className="text-muted-foreground font-medium mb-2">
                      Preview Disabled for Protected Documents
                    </p>
                    <p className="text-sm text-muted-foreground">
                      This document has been marked as protected by the uploader.
                      Preview is disabled to prevent unauthorized access. If you
                      need access, please contact the document owner or your
                      administrator.
                    </p>
                  </div>
                </div>
              ) : docData.s3_url ? (
                <SecureDocumentViewer
                  url={docData.s3_url}
                  fileType={docData.file_type}
                  userName={user?.name || user?.email}
                />
              ) : (
                <div className="aspect-[4/3] bg-muted/50 rounded-lg flex items-center justify-center border border-border/50">
                  <div className="text-center p-6">
                    <FileText className="h-16 w-16 mx-auto mb-4 text-muted-foreground/50" />
                    <p className="text-muted-foreground font-medium">
                      Preview not available
                    </p>
                    <p className="text-sm text-muted-foreground mt-2">
                      File not found in storage.
                    </p>
                  </div>
                </div>
              )}
            </TabsContent>

            <TabsContent value="chat" className="p-6 m-0">
              <DocumentChatPanel documentId={id} />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};
