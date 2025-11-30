import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Download,
  Eye,
  FileText,
  Calendar,
  Building2,
  Shield,
  Star,
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

export const DocumentDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  // const [document, setDocument] = useState(null);
  const [docData, setDocData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isBookmarked, setIsBookmarked] = useState(false);

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

  if (loading) {
    return <LoadingSpinner text="Loading document..." />;
  }

  if (!document) {
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

      {/* Preview Card */}
      <Card className="glass-card border-border/50">
        <CardHeader>
          <CardTitle>Document Preview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="aspect-[4/3] bg-muted/50 rounded-lg flex items-center justify-center border border-border/50">
            <div className="text-center p-6">
              <FileText className="h-16 w-16 mx-auto mb-4 text-muted-foreground/50" />
              <p className="text-muted-foreground font-medium">
                Preview not available
              </p>
              <p className="text-sm text-muted-foreground mt-2">
                {document.download_allowed
                  ? "Download the file to view its full content."
                  : "This document is protected and cannot be previewed."}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
