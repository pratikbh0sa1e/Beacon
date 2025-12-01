import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Grid3x3,
  List,
  Download,
  Eye,
  Star,
  FileText,
  Search,
  ArrowUpDown,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { documentAPI, bookmarkAPI } from "../services/api";
import { PageHeader } from "../components/common/PageHeader";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { EmptyState } from "../components/common/EmptyState";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardContent } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { formatRelativeTime } from "../utils/dateFormat";
import { toast } from "sonner";

export const BookmarksPage = () => {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState([]);
  const [filteredDocuments, setFilteredDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState("grid");
  const [searchTerm, setSearchTerm] = useState("");
  const [sortBy, setSortBy] = useState("recent");

  useEffect(() => {
    fetchBookmarks();
  }, []);

  useEffect(() => {
    filterAndSortDocuments();
  }, [documents, searchTerm, sortBy]);

  const fetchBookmarks = async () => {
    setLoading(true);
    try {
      // 1. Get list of bookmarked IDs
      const bookmarkResponse = await bookmarkAPI.list();
      const bookmarkedIds = bookmarkResponse.data;

      if (bookmarkedIds.length === 0) {
        setDocuments([]);
        setFilteredDocuments([]);
        return;
      }

      // 2. Fetch all documents (ideally backend would have a filter for this,
      // but for now we can filter client-side or fetch individually if list is small)
      // Better approach: Update backend to accept a list of IDs or a 'bookmarked_only' flag.
      // For now, let's assume we fetch the list and filter.
      // Optimization: Add `bookmarked_only=true` to listDocuments API in backend.

      // Current workaround: Fetch individual documents (Okay for small numbers, bad for scaling)
      // OR Fetch all and filter (Better if total docs isn't huge)

      const docsResponse = await documentAPI.listDocuments({ limit: 1000 }); // Fetch a batch
      const allDocs = docsResponse.data.documents;

      const bookmarkedDocs = allDocs.filter((doc) =>
        bookmarkedIds.includes(doc.id)
      );
      setDocuments(bookmarkedDocs);
    } catch (error) {
      console.error("Error fetching bookmarks:", error);
      toast.error("Failed to load bookmarks");
    } finally {
      setLoading(false);
    }
  };

  const filterAndSortDocuments = () => {
    let filtered = [...documents];

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(
        (doc) =>
          doc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
          doc.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          doc.department?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Apply sorting
    switch (sortBy) {
      case "recent":
        filtered.sort(
          (a, b) => new Date(b.updated_at) - new Date(a.updated_at)
        );
        break;
      case "oldest":
        filtered.sort(
          (a, b) => new Date(a.updated_at) - new Date(b.updated_at)
        );
        break;
      case "title-asc":
        filtered.sort((a, b) => a.title.localeCompare(b.title));
        break;
      case "title-desc":
        filtered.sort((a, b) => b.title.localeCompare(a.title));
        break;
      case "department":
        filtered.sort((a, b) =>
          (a.department || "").localeCompare(b.department || "")
        );
        break;
      default:
        break;
    }

    setFilteredDocuments(filtered);
  };

  const handleDownload = async (docId, title) => {
    try {
      const response = await documentAPI.downloadDocument(docId);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", title);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success("Document downloaded successfully");
    } catch (error) {
      console.error("Download error:", error);
      toast.error("Failed to download document");
    }
  };

  const removeBookmark = async (e, docId) => {
    e.stopPropagation();
    try {
      await bookmarkAPI.toggle(docId);
      setDocuments((prev) => prev.filter((doc) => doc.id !== docId));
      toast.success("Bookmark removed");
    } catch (error) {
      toast.error("Failed to remove bookmark");
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Bookmarked Documents"
        description="Your saved documents for quick access"
        icon={Star}
      />

      <Card className="glass-card border-border/50">
        <CardContent className="p-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search bookmarked documents..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={sortBy} onValueChange={setSortBy}>
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

      {loading ? (
        <LoadingSpinner text="Loading bookmarks..." />
      ) : documents.length === 0 ? (
        <EmptyState
          title="No bookmarks yet"
          description="Star documents to see them here for quick access."
          action={() => navigate("/documents")}
          actionLabel="Browse Documents"
        />
      ) : filteredDocuments.length === 0 ? (
        <EmptyState
          title="No documents found"
          description="Try adjusting your search term."
          action={() => setSearchTerm("")}
          actionLabel="Clear Search"
        />
      ) : (
        <div
          className={
            viewMode === "grid"
              ? "grid gap-6 md:grid-cols-2 lg:grid-cols-3"
              : "space-y-4"
          }
        >
          {filteredDocuments.map((doc, index) => (
            <motion.div
              key={doc.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <Card className="glass-card border-border/50 hover:border-primary/50 h-full flex flex-col transition-all duration-300 hover:shadow-lg">
                <CardContent className="p-6 flex flex-col flex-1">
                  <div className="flex items-start justify-between mb-4">
                    <Badge variant="outline">{doc.category}</Badge>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-yellow-500 hover:text-yellow-600 hover:bg-yellow-500/10"
                      onClick={(e) => removeBookmark(e, doc.id)}
                    >
                      <Star className="h-5 w-5 fill-current" />
                    </Button>
                  </div>
                  <h3
                    className="font-semibold text-lg mb-2 line-clamp-2"
                    title={doc.title}
                  >
                    {doc.title}
                  </h3>
                  <p className="text-sm text-muted-foreground mb-4 line-clamp-3 flex-1">
                    {doc.description || "No description available"}
                  </p>
                  <div className="space-y-2 text-xs text-muted-foreground mb-4">
                    <p>Department: {doc.department}</p>
                    <p>Updated: {formatRelativeTime(doc.updated_at)}</p>
                  </div>
                  <div className="flex gap-2 mt-auto">
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      onClick={() => navigate(`/documents/${doc.id}`)}
                    >
                      <Eye className="h-4 w-4 mr-2" />
                      View
                    </Button>
                    {doc.download_allowed && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1"
                        onClick={() => handleDownload(doc.id, doc.title)}
                      >
                        <Download className="h-4 w-4 mr-2" />
                        Download
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
};

// Helper function if not imported
// function formatRelativeTime(dateString) {
//   if (!dateString) return '';
//   const date = new Date(dateString);
//   const now = new Date();
//   const diff = now - date;
//   const days = Math.floor(diff / (1000 * 60 * 60 * 24));

//   if (days === 0) return 'Today';
//   if (days === 1) return 'Yesterday';
//   if (days < 30) return `${days} days ago`;
//   return date.toLocaleDateString();
// }
