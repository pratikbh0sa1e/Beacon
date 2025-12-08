import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Search,
  Filter,
  Grid3x3,
  List,
  Download,
  Eye,
  ChevronLeft,
  ChevronRight,
  Star,
  ArrowUpDown,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { documentAPI, bookmarkAPI } from "../../services/api";
import { PageHeader } from "../../components/common/PageHeader";
import { LoadingSpinner } from "../../components/common/LoadingSpinner";
import { EmptyState } from "../../components/common/EmptyState";
import { Input } from "../../components/ui/input";
import { Button } from "../../components/ui/button";
import { Card, CardContent } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
// import { formatRelativeTime } from "../../utils/dateFormat"; // Ensure you have this utility or import it
import { DOCUMENT_CATEGORIES } from "../../constants/categories";
import { toast } from "sonner";
import { OCRBadge } from "../../components/ocr";

export const DocumentExplorerPage = () => {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState("grid");

  // Pagination & Filter State
  const [searchTerm, setSearchTerm] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [sortBy, setSortBy] = useState("recent");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const ITEMS_PER_PAGE = 9;

  // Bookmark State
  const [bookmarkedIds, setBookmarkedIds] = useState([]);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setPage(1);
      fetchDocuments();
    }, 500);
    return () => clearTimeout(timer);
  }, [searchTerm, categoryFilter, sortBy]);

  // Fetch when page changes
  useEffect(() => {
    fetchDocuments();
  }, [page]);

  // Initial fetch for bookmarks
  useEffect(() => {
    fetchBookmarks();
  }, []);

  const fetchBookmarks = async () => {
    try {
      const response = await bookmarkAPI.list();
      setBookmarkedIds(response.data);
    } catch (error) {
      console.error("Error fetching bookmarks:", error);
    }
  };

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const offset = (page - 1) * ITEMS_PER_PAGE;

      const response = await documentAPI.listDocuments({
        category: categoryFilter !== "all" ? categoryFilter : undefined,
        search: searchTerm || undefined,
        sort_by: sortBy || undefined,
        limit: ITEMS_PER_PAGE,
        offset: offset,
      });

      const docs = response.data?.documents || [];
      const total = response.data?.total || 0;

      setDocuments(docs);
      setTotalPages(Math.ceil(total / ITEMS_PER_PAGE));
    } catch (error) {
      console.error("Error fetching documents:", error);
      toast.error("Failed to load documents");
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (docId, title) => {
    try {
      const response = await documentAPI.downloadDocument(docId);

      // Extract filename from Content-Disposition header if available
      const contentDisposition = response.headers["content-disposition"];
      let filename = title;

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

  const toggleBookmark = async (e, docId) => {
    e.stopPropagation();
    try {
      const response = await bookmarkAPI.toggle(docId);
      if (response.data.status === "added") {
        setBookmarkedIds((prev) => [...prev, docId]);
        toast.success("Bookmark added");
      } else {
        setBookmarkedIds((prev) => prev.filter((id) => id !== docId));
        toast.success("Bookmark removed");
      }
    } catch (error) {
      toast.error("Failed to update bookmark");
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Document Explorer"
        description="Browse, search, and access your document library"
        icon={Grid3x3}
        action={
          <Button onClick={() => navigate("/upload")} className="neon-glow">
            Upload Document
          </Button>
        }
      />

      {/* Filters & Search */}
      <Card className="glass-card border-border/50">
        <CardContent className="p-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search documents by title or summary..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select
              value={categoryFilter}
              onValueChange={(v) => {
                setCategoryFilter(v);
                setPage(1);
              }}
            >
              <SelectTrigger className="w-full sm:w-48">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                {DOCUMENT_CATEGORIES.map((cat) => (
                  <SelectItem key={cat} value={cat}>
                    {cat}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select
              value={sortBy}
              onValueChange={(v) => {
                setSortBy(v);
                setPage(1);
              }}
            >
              <SelectTrigger className="w-full sm:w-48">
                <ArrowUpDown className="h-4 w-4 mr-2" />
                <SelectValue placeholder="Sort by" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="recent">Most Recent</SelectItem>
                <SelectItem value="oldest">Oldest First</SelectItem>
                <SelectItem value="title-asc">Title (A-Z)</SelectItem>
                <SelectItem value="title-desc">Title (Z-A)</SelectItem>
                <SelectItem value="department">Department</SelectItem>
              </SelectContent>
            </Select>
            <div className="flex gap-2">
              <Button
                variant={viewMode === "grid" ? "default" : "outline"}
                size="icon"
                onClick={() => setViewMode("grid")}
              >
                <Grid3x3 className="h-4 w-4" />
              </Button>
              <Button
                variant={viewMode === "list" ? "default" : "outline"}
                size="icon"
                onClick={() => setViewMode("list")}
              >
                <List className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Content Area */}
      {loading ? (
        <LoadingSpinner text="Loading documents..." />
      ) : documents.length === 0 ? (
        <EmptyState
          title="No documents found"
          description="Try adjusting your search or category filter."
          action={() => {
            setSearchTerm("");
            setCategoryFilter("all");
          }}
          actionLabel="Clear Filters"
        />
      ) : (
        <>
          <div
            className={
              viewMode === "grid"
                ? "grid gap-6 md:grid-cols-2 lg:grid-cols-3"
                : "space-y-4"
            }
          >
            {documents.map((doc, index) => {
              const isBookmarked = bookmarkedIds.includes(doc.id);

              return (
                <motion.div
                  key={doc.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Card
                    className="glass-card border-border/50 hover:border-primary/50 h-full flex flex-col transition-all duration-300 hover:shadow-lg cursor-pointer"
                    onClick={() => navigate(`/documents/${doc.id}`)}
                  >
                    <CardContent className="p-6 flex flex-col flex-1">
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex flex-col gap-2">
                          <Badge variant="outline">{doc.category}</Badge>
                          {/* Approval Status Badge */}
                          {doc.approval_status && (
                            <Badge
                              className={
                                doc.approval_status === "approved"
                                  ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                                  : doc.approval_status === "pending"
                                    ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
                                    : doc.approval_status === "rejected"
                                      ? "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
                                      : doc.approval_status === "draft"
                                        ? "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200"
                                        : "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
                              }
                            >
                              {doc.approval_status
                                .replace("_", " ")
                                .toUpperCase()}
                            </Badge>
                          )}
                        </div>
                        {/* OCR Badge */}
                        <OCRBadge document={doc} />
                        <div className="flex gap-2">
                          <Badge
                            variant={
                              doc.visibility === "public"
                                ? "default"
                                : "secondary"
                            }
                          >
                            {doc.visibility}
                          </Badge>
                          <Button
                            variant="ghost"
                            size="icon"
                            className={`h-6 w-6 ${isBookmarked
                              ? "text-yellow-500 hover:text-yellow-600 hover:bg-yellow-500/10"
                              : "text-muted-foreground"
                              }`}
                            onClick={(e) => toggleBookmark(e, doc.id)}
                          >
                            <Star
                              className={`h-4 w-4 ${isBookmarked ? "fill-current" : ""
                                }`}
                            />
                          </Button>
                        </div>
                      </div>

                      <h3
                        className="font-semibold text-lg mb-2 line-clamp-2"
                        title={doc.title}
                      >
                        {doc.title}
                      </h3>

                      {/* Uploader Info */}
                      {doc.uploader && (
                        <div className="flex items-center gap-2 mb-3">
                          <div className="h-6 w-6 rounded-full bg-secondary flex items-center justify-center text-xs font-bold">
                            {doc.uploader.name.charAt(0)}
                          </div>
                          <div className="flex flex-col">
                            <span className="text-xs font-medium">
                              {doc.uploader.name}
                            </span>
                            <span className="text-[10px] text-muted-foreground capitalize">
                              {doc.uploader.role
                                ? doc.uploader.role.replace("_", " ")
                                : "Unknown Role"}
                            </span>
                          </div>
                        </div>
                      )}

                      <p className="text-sm text-muted-foreground mb-4 line-clamp-3 flex-1">
                        {doc.description || "No description available"}
                      </p>

                      <div className="space-y-2 text-xs text-muted-foreground mb-4">
                        <p>Department: {doc.department}</p>
                        <p>Year: {doc.year}</p>
                        <p>
                          Updated:{" "}
                          {formatRelativeTime
                            ? formatRelativeTime(doc.updated_at)
                            : doc.updated_at}
                        </p>
                      </div>

                      <div className="flex gap-2 mt-auto">
                        <Button
                          variant="outline"
                          size="sm"
                          className="flex-1"
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/documents/${doc.id}`);
                          }}
                        >
                          <Eye className="h-4 w-4 mr-2" />
                          View
                        </Button>
                        {doc.download_allowed && (
                          <Button
                            variant="outline"
                            size="sm"
                            className="flex-1"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDownload(doc.id, doc.title);
                            }}
                          >
                            <Download className="h-4 w-4 mr-2" />
                            Download
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })}
          </div>

          {/* Pagination Controls */}
          <div className="flex items-center justify-between pt-4 border-t border-border/40">
            <p className="text-sm text-muted-foreground">
              Page {page} of {totalPages}
            </p>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                <ChevronLeft className="h-4 w-4 mr-2" />
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
              >
                Next
                <ChevronRight className="h-4 w-4 ml-2" />
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

// Helper function if not imported
function formatRelativeTime(dateString) {
  if (!dateString) return "";
  const date = new Date(dateString);
  const now = new Date();
  const diff = now - date;
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));

  if (days === 0) return "Today";
  if (days === 1) return "Yesterday";
  if (days < 30) return `${days} days ago`;
  return date.toLocaleDateString();
}
