import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Globe,
  Plus,
  Play,
  Pause,
  Trash2,
  Eye,
  Pencil,
  CheckCircle,
  XCircle,
  Clock,
  Download,
  AlertCircle,
  TrendingUp,
  FileText,
  Shield,
  Zap,
  Settings,
  Activity,
} from "lucide-react";
import ScrapingLogs from "../../components/ScrapingLogs.jsx";
import { PageHeader } from "../../components/common/PageHeader";
import { LoadingSpinner } from "../../components/common/LoadingSpinner";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../../components/ui/dialog";
import { toast } from "sonner";
import axios from "axios";
import api from "../../services/api";

const API_BASE_URL = `${
  import.meta.env.VITE_API_URL || "http://localhost:8000"
}/api`;

export const WebScrapingPage = () => {
  const [loading, setLoading] = useState(true);
  const [sources, setSources] = useState([]);
  const [stats, setStats] = useState(null);
  const [logs, setLogs] = useState([]);
  const [scrapedDocs, setScrapedDocs] = useState([]);
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isPreviewDialogOpen, setIsPreviewDialogOpen] = useState(false);
  const [previewData, setPreviewData] = useState(null);
  const [scrapingInProgress, setScrapingInProgress] = useState({});
  const [searchKeyword, setSearchKeyword] = useState("");
  const [editingSource, setEditingSource] = useState(null);
  const [selectedDocs, setSelectedDocs] = useState([]); // For AI analysis
  const [analyzing, setAnalyzing] = useState(false); // Track analysis state
  const [scrapingJobs, setScrapingJobs] = useState({}); // Track active scraping jobs
  const [availableScrapers, setAvailableScrapers] = useState({}); // Available site-specific scrapers

  // Form state
  const [newSource, setNewSource] = useState({
    name: "",
    url: "",
    description: "",
    keywords: "",
    max_documents: 1500,
    pagination_enabled: true,
    max_pages: 100,
    scraper_type: "generic", // NEW: Site-specific scraper selection
    window_size: 3, // NEW: Sliding window size
    force_full_scan: false, // NEW: Force full scan option
  });

  // View state
  const [activeView, setActiveView] = useState("sources"); // "sources" or "logs"

  const navigate = useNavigate();

  useEffect(() => {
    fetchData();
    fetchAvailableScrapers();
  }, []);

  const fetchAvailableScrapers = async () => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/enhanced-web-scraping/available-scrapers`
      );
      setAvailableScrapers(response.data);
    } catch (error) {
      console.error("Error fetching available scrapers:", error);
      // Set default scrapers if API fails
      setAvailableScrapers({
        generic: "Generic Government Site",
        moe: "Ministry of Education",
        ugc: "University Grants Commission",
        aicte: "All India Council for Technical Education",
      });
    }
  };

  const fetchData = async () => {
    try {
      setLoading(true);
      const [sourcesRes, statsRes, logsRes, docsRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/web-scraping/sources`),
        axios.get(`${API_BASE_URL}/web-scraping/stats`),
        axios.get(`${API_BASE_URL}/web-scraping/logs?limit=10`),
        axios.get(`${API_BASE_URL}/web-scraping/scraped-documents?limit=1000`),
      ]);

      setSources(sourcesRes.data);
      setStats(statsRes.data);
      setLogs(logsRes.data);
      setScrapedDocs(docsRes.data);
    } catch (error) {
      console.error("Error fetching data:", error);
      toast.error("Failed to load web scraping data");
    } finally {
      setLoading(false);
    }
  };

  const handleAddSource = async () => {
    try {
      const keywords = newSource.keywords
        ? newSource.keywords.split(",").map((k) => k.trim())
        : null;

      await axios.post(`${API_BASE_URL}/web-scraping/sources`, {
        name: newSource.name,
        url: newSource.url,
        description: newSource.description,
        keywords: keywords,
        max_documents: parseInt(newSource.max_documents),
        pagination_enabled: newSource.pagination_enabled,
        max_pages: parseInt(newSource.max_pages),
        scraping_enabled: true,
        // Enhanced fields
        scraper_type: newSource.scraper_type,
        window_size: newSource.window_size,
        force_full_scan: newSource.force_full_scan,
      });

      toast.success("Enhanced source added successfully!");
      setIsAddDialogOpen(false);
      setNewSource({
        name: "",
        url: "",
        description: "",
        keywords: "",
        max_documents: 1500,
        pagination_enabled: true,
        max_pages: 100,
        scraper_type: "generic",
        window_size: 3,
        force_full_scan: false,
      });
      fetchData();
    } catch (error) {
      console.error("Error adding source:", error);
      toast.error(error.response?.data?.detail || "Failed to add source");
    }
  };

  const handlePreview = async (url) => {
    try {
      setPreviewData(null);
      setIsPreviewDialogOpen(true);
      const response = await axios.post(
        `${API_BASE_URL}/web-scraping/preview`,
        {
          url: url,
        }
      );
      setPreviewData(response.data);
    } catch (error) {
      console.error("Error previewing source:", error);
      toast.error("Failed to preview source");
      setIsPreviewDialogOpen(false);
    }
  };

  const handleScrapeNow = async (sourceId) => {
    try {
      setScrapingInProgress((prev) => ({ ...prev, [sourceId]: true }));

      // Generate a unique job ID for this scraping operation
      const jobId = `scrape_${sourceId}_${Date.now()}`;
      setScrapingJobs((prev) => ({ ...prev, [sourceId]: jobId }));

      toast.info("Enhanced scraping started...");

      // Get source to check settings
      const source = sources.find((s) => s.id === sourceId);

      // Use enhanced scraping endpoint
      const response = await axios.post(
        `${API_BASE_URL}/enhanced-web-scraping/scrape-enhanced`,
        {
          source_id: sourceId,
          keywords: source?.keywords || null,
          max_documents: source?.max_documents || 1500,
          pagination_enabled: source?.pagination_enabled !== false,
          max_pages: source?.max_pages || 100,
          incremental: true, // Use incremental by default
        }
      );

      // Show enhanced results
      const result = response.data;
      const successMsg = `Enhanced scraping complete: ${
        result.documents_new || 0
      } new, ${result.documents_updated || 0} updated, ${
        result.documents_skipped || 0
      } skipped`;

      toast.success(successMsg, {
        description: `Scraper: ${result.scraper_used || "Enhanced"}, Time: ${
          result.execution_time?.toFixed(1) || 0
        }s`,
        duration: 5000,
      });

      // Wait a moment then refresh to get new documents
      setTimeout(() => {
        fetchData();
      }, 500);
    } catch (error) {
      console.error("Error scraping:", error);

      // Check if it was cancelled
      if (error.response?.status === 499 || error.message?.includes("cancel")) {
        toast.info("Scraping was cancelled");
      } else {
        toast.error(error.response?.data?.detail || "Enhanced scraping failed");
      }
    } finally {
      setScrapingInProgress((prev) => ({ ...prev, [sourceId]: false }));
      setScrapingJobs((prev) => {
        const newJobs = { ...prev };
        delete newJobs[sourceId];
        return newJobs;
      });
    }
  };

  const handleStopScraping = async (sourceId) => {
    try {
      const jobId = scrapingJobs[sourceId];
      if (!jobId) {
        toast.error("No active scraping job found");
        return;
      }

      // Call stop endpoint (we'll create this)
      await axios.post(`${API_BASE_URL}/enhanced-web-scraping/stop-scraping`, {
        source_id: sourceId,
        job_id: jobId,
      });

      toast.success("Scraping stopped successfully");

      // Update state
      setScrapingInProgress((prev) => ({ ...prev, [sourceId]: false }));
      setScrapingJobs((prev) => {
        const newJobs = { ...prev };
        delete newJobs[sourceId];
        return newJobs;
      });
    } catch (error) {
      console.error("Error stopping scraping:", error);
      toast.error("Failed to stop scraping");
    }
  };

  const handleEditSource = (source) => {
    setEditingSource(source);
    setNewSource({
      name: source.name,
      url: source.url,
      description: source.description || "",
      keywords: source.keywords ? source.keywords.join(", ") : "",
      max_documents: source.max_documents || 1500,
      pagination_enabled: source.pagination_enabled !== false,
      max_pages: source.max_pages || 100,
      scraper_type: source.scraper_type || "generic",
      window_size: source.window_size || 3,
      force_full_scan: false, // Always default to false for editing
    });
    setIsEditDialogOpen(true);
  };

  const handleUpdateSource = async () => {
    try {
      const keywords = newSource.keywords
        ? newSource.keywords.split(",").map((k) => k.trim())
        : null;

      await axios.put(
        `${API_BASE_URL}/web-scraping/sources/${editingSource.id}`,
        {
          name: newSource.name,
          url: newSource.url,
          description: newSource.description,
          keywords: keywords,
          max_documents: parseInt(newSource.max_documents),
          pagination_enabled: newSource.pagination_enabled,
          max_pages: parseInt(newSource.max_pages),
          scraping_enabled: true,
          // Enhanced fields
          scraper_type: newSource.scraper_type,
          window_size: newSource.window_size,
        }
      );

      toast.success("Enhanced source updated successfully!");
      setIsEditDialogOpen(false);
      setEditingSource(null);
      setNewSource({
        name: "",
        url: "",
        description: "",
        keywords: "",
        max_documents: 1500,
        pagination_enabled: true,
        max_pages: 100,
        scraper_type: "generic",
        window_size: 3,
        force_full_scan: false,
      });
      fetchData();
    } catch (error) {
      console.error("Error updating source:", error);
      toast.error(error.response?.data?.detail || "Failed to update source");
    }
  };

  const handleDeleteSource = async (sourceId) => {
    if (!confirm("Are you sure you want to delete this source?")) return;

    try {
      await axios.delete(`${API_BASE_URL}/web-scraping/sources/${sourceId}`);
      toast.success("Source deleted successfully!");
      fetchData();
    } catch (error) {
      console.error("Error deleting source:", error);
      toast.error("Failed to delete source");
    }
  };

  const handleQuickDemo = async () => {
    try {
      toast.info("Running demo scrape on UGC website...");
      const response = await axios.post(
        `${API_BASE_URL}/web-scraping/demo/education-gov`
      );

      console.log("Demo response:", response.data);

      toast.success(response.data.message);

      // Wait a moment then refresh to show new documents
      setTimeout(() => {
        fetchData();
      }, 500);
    } catch (error) {
      console.error("Error running demo:", error);
      toast.error(error.response?.data?.detail || "Demo failed");
    }
  };

  // AI Analysis handlers
  const handleToggleDocSelection = (doc) => {
    setSelectedDocs((prev) => {
      const isSelected = prev.some((d) => d.url === doc.url);
      if (isSelected) {
        return prev.filter((d) => d.url !== doc.url);
      } else {
        return [...prev, doc];
      }
    });
  };

  const handleAnalyzeWithAI = async () => {
    if (selectedDocs.length === 0) {
      toast.error("Please select at least one document to analyze");
      return;
    }

    try {
      setAnalyzing(true);

      // Show progress toast with more details
      const toastId = toast.loading(
        `🔄 Processing ${selectedDocs.length} document${
          selectedDocs.length > 1 ? "s" : ""
        }...`,
        {
          duration: Infinity,
          description: "Downloading, extracting text, and analyzing with AI",
        }
      );

      // Call backend to download, extract, and analyze (using authenticated api)
      const response = await api.post(`/api/document-analysis/analyze`, {
        document_urls: selectedDocs.map((d) => d.url),
        document_titles: selectedDocs.map((d) => d.title),
        analysis_type: "decision_support",
      });

      const { analysis, documents_processed, total_chunks, ocr_used_count } =
        response.data;

      // Dismiss loading toast
      toast.dismiss(toastId);

      // Store analysis result for AI chat with metadata
      sessionStorage.setItem(
        "analysisResult",
        JSON.stringify({
          analysis,
          documents: selectedDocs.map((d) => d.title),
          documents_processed,
          total_chunks,
          ocr_used_count,
          timestamp: new Date().toISOString(),
        })
      );

      // Show detailed success message
      const successMsg =
        ocr_used_count > 0
          ? `✅ Analysis Complete! Processed ${documents_processed} documents (OCR used on ${ocr_used_count})`
          : `✅ Analysis Complete! Processed ${documents_processed} documents`;

      toast.success(successMsg, {
        description: `${total_chunks} text chunks analyzed. Redirecting to AI Chat...`,
        duration: 3000,
      });

      // Navigate after a brief delay to show the success message
      setTimeout(() => {
        navigate("/ai-chat");
      }, 1000);
    } catch (error) {
      console.error("Error analyzing documents:", error);
      const errorDetail =
        error.response?.data?.detail || "Analysis failed. Please try again.";
      toast.error("Analysis Failed", {
        description: errorDetail,
        duration: 5000,
      });
    } finally {
      setAnalyzing(false);
    }
  };

  const getCredibilityColor = (score) => {
    if (score >= 9) return "bg-green-500";
    if (score >= 7) return "bg-blue-500";
    if (score >= 5) return "bg-yellow-500";
    return "bg-red-500";
  };

  const getStatusColor = (status) => {
    if (status === "success") return "bg-green-500";
    if (status === "failed") return "bg-red-500";
    return "bg-gray-500";
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <PageHeader
        title="Web Scraping"
        description="Automated document ingestion from government websites"
        icon={Globe}
      />

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Total Sources
              </CardTitle>
              <Globe className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {stats?.total_sources || 0}
              </div>
              <p className="text-xs text-muted-foreground">
                {stats?.enabled_sources || 0} enabled
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Total Scrapes
              </CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {stats?.total_scrapes || 0}
              </div>
              <p className="text-xs text-muted-foreground">
                {stats?.successful_scrapes || 0} successful
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Documents Scraped
              </CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {stats?.total_documents_scraped || 0}
              </div>
              <p className="text-xs text-muted-foreground">
                {stats?.scraped_documents_available || 0} available
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Success Rate
              </CardTitle>
              <CheckCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {stats?.total_scrapes > 0
                  ? Math.round(
                      (stats.successful_scrapes / stats.total_scrapes) * 100
                    )
                  : 0}
                %
              </div>
              <p className="text-xs text-muted-foreground">
                {stats?.failed_scrapes || 0} failed
              </p>
            </CardContent>
          </Card>
        </motion.div>

        {stats?.filtering_stats &&
          stats.filtering_stats.scrapes_with_keywords > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
            >
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    Filter Match Rate
                  </CardTitle>
                  <Zap className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {stats.filtering_stats.average_match_rate_percent?.toFixed(
                      1
                    ) || 0}
                    %
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {stats.filtering_stats.total_documents_skipped || 0}{" "}
                    filtered out
                  </p>
                </CardContent>
              </Card>
            </motion.div>
          )}
      </div>

      {/* View Toggle */}
      <div className="flex gap-2 mb-6">
        <Button
          variant={activeView === "sources" ? "default" : "outline"}
          onClick={() => setActiveView("sources")}
        >
          <Settings className="mr-2 h-4 w-4" />
          Sources & Configuration
        </Button>
        <Button
          variant={activeView === "logs" ? "default" : "outline"}
          onClick={() => setActiveView("logs")}
        >
          <Activity className="mr-2 h-4 w-4" />
          Scraping Logs
        </Button>
      </div>

      {/* Show Logs View */}
      {activeView === "logs" && <ScrapingLogs />}

      {/* Show Sources View */}
      {activeView === "sources" && (
        <>
          {/* Action Buttons */}
          <div className="flex gap-4 mb-6">
            <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  Add Source
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[525px]">
                <DialogHeader>
                  <DialogTitle>Add Web Scraping Source</DialogTitle>
                  <DialogDescription>
                    Add a new government website to scrape for documents
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid gap-2">
                    <Label htmlFor="name">Source Name</Label>
                    <Input
                      id="name"
                      placeholder="e.g., UGC Official Website"
                      value={newSource.name}
                      onChange={(e) =>
                        setNewSource({ ...newSource, name: e.target.value })
                      }
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="url">URL</Label>
                    <Input
                      id="url"
                      placeholder="https://www.ugc.gov.in/"
                      value={newSource.url}
                      onChange={(e) =>
                        setNewSource({ ...newSource, url: e.target.value })
                      }
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="description">Description (Optional)</Label>
                    <Input
                      id="description"
                      placeholder="Official UGC website for policies and circulars"
                      value={newSource.description}
                      onChange={(e) =>
                        setNewSource({
                          ...newSource,
                          description: e.target.value,
                        })
                      }
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="keywords">
                      Keywords (Optional) - Filter documents during scraping
                    </Label>
                    <Input
                      id="keywords"
                      placeholder="policy, circular, notification, fee, admission (comma-separated)"
                      value={newSource.keywords}
                      onChange={(e) =>
                        setNewSource({ ...newSource, keywords: e.target.value })
                      }
                    />
                    <p className="text-xs text-muted-foreground">
                      Only documents containing these keywords will be scraped.
                      Leave empty to scrape all documents.
                    </p>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="scraper_type">Site-Specific Scraper</Label>
                    <select
                      id="scraper_type"
                      value={newSource.scraper_type}
                      onChange={(e) =>
                        setNewSource({
                          ...newSource,
                          scraper_type: e.target.value,
                        })
                      }
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      <option value="generic">Generic Government Site</option>
                      <option value="moe">Ministry of Education</option>
                      <option value="ugc">University Grants Commission</option>
                      <option value="aicte">
                        All India Council for Technical Education
                      </option>
                    </select>
                    <p className="text-xs text-muted-foreground">
                      Choose the appropriate scraper for better extraction
                      accuracy
                    </p>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="window_size">Sliding Window Size</Label>
                    <Input
                      id="window_size"
                      type="number"
                      min="1"
                      max="10"
                      value={newSource.window_size}
                      onChange={(e) =>
                        setNewSource({
                          ...newSource,
                          window_size: parseInt(e.target.value) || 3,
                        })
                      }
                    />
                    <p className="text-xs text-muted-foreground">
                      Number of recent pages to always re-scan (default: 3)
                    </p>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="force_full_scan">Scanning Mode</Label>
                    <div className="flex items-center gap-2">
                      <input
                        id="force_full_scan"
                        type="checkbox"
                        checked={newSource.force_full_scan}
                        onChange={(e) =>
                          setNewSource({
                            ...newSource,
                            force_full_scan: e.target.checked,
                          })
                        }
                        className="h-4 w-4"
                      />
                      <span className="text-sm">
                        Force full scan (ignore incremental optimizations)
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Enable for first-time scraping or when major changes are
                      expected
                    </p>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="max_docs">Max Documents per Scrape</Label>
                    <Input
                      id="max_docs"
                      type="number"
                      value={newSource.max_documents}
                      onChange={(e) =>
                        setNewSource({
                          ...newSource,
                          max_documents: parseInt(e.target.value) || 1500,
                        })
                      }
                    />
                    <p className="text-xs text-muted-foreground">
                      Default: 1500 documents. Increase for larger scrapes.
                    </p>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="pagination">Enable Pagination</Label>
                    <div className="flex items-center gap-2">
                      <input
                        id="pagination"
                        type="checkbox"
                        checked={newSource.pagination_enabled}
                        onChange={(e) =>
                          setNewSource({
                            ...newSource,
                            pagination_enabled: e.target.checked,
                          })
                        }
                        className="h-4 w-4"
                      />
                      <span className="text-sm">
                        Automatically follow pagination links
                      </span>
                    </div>
                  </div>
                  {newSource.pagination_enabled && (
                    <div className="grid gap-2">
                      <Label htmlFor="max_pages">Max Pages to Scrape</Label>
                      <Input
                        id="max_pages"
                        type="number"
                        value={newSource.max_pages}
                        onChange={(e) =>
                          setNewSource({
                            ...newSource,
                            max_pages: e.target.value,
                          })
                        }
                      />
                      <p className="text-xs text-muted-foreground">
                        Maximum number of pages to follow (default: 100)
                      </p>
                    </div>
                  )}
                </div>
                <DialogFooter>
                  <Button
                    variant="outline"
                    onClick={() => setIsAddDialogOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button onClick={handleAddSource}>Add Source</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>

            {/* Edit Source Dialog */}
            <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
              <DialogContent className="sm:max-w-[525px]">
                <DialogHeader>
                  <DialogTitle>Edit Web Scraping Source</DialogTitle>
                  <DialogDescription>
                    Update the source details and keywords
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid gap-2">
                    <Label htmlFor="edit-name">Source Name</Label>
                    <Input
                      id="edit-name"
                      placeholder="e.g., UGC Official Website"
                      value={newSource.name}
                      onChange={(e) =>
                        setNewSource({ ...newSource, name: e.target.value })
                      }
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="edit-url">URL</Label>
                    <Input
                      id="edit-url"
                      placeholder="https://www.ugc.gov.in/"
                      value={newSource.url}
                      onChange={(e) =>
                        setNewSource({ ...newSource, url: e.target.value })
                      }
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="edit-description">
                      Description (Optional)
                    </Label>
                    <Input
                      id="edit-description"
                      placeholder="Official UGC website for policies and circulars"
                      value={newSource.description}
                      onChange={(e) =>
                        setNewSource({
                          ...newSource,
                          description: e.target.value,
                        })
                      }
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="edit-keywords">
                      Keywords (Optional) - Filter documents during scraping
                    </Label>
                    <Input
                      id="edit-keywords"
                      placeholder="policy, circular, notification, report (comma-separated)"
                      value={newSource.keywords}
                      onChange={(e) =>
                        setNewSource({ ...newSource, keywords: e.target.value })
                      }
                    />
                    <p className="text-xs text-muted-foreground">
                      Change keywords to filter different types of documents.
                      Leave empty to scrape all documents.
                    </p>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="edit-scraper_type">
                      Site-Specific Scraper
                    </Label>
                    <select
                      id="edit-scraper_type"
                      value={newSource.scraper_type}
                      onChange={(e) =>
                        setNewSource({
                          ...newSource,
                          scraper_type: e.target.value,
                        })
                      }
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      <option value="generic">Generic Government Site</option>
                      <option value="moe">Ministry of Education</option>
                      <option value="ugc">University Grants Commission</option>
                      <option value="aicte">
                        All India Council for Technical Education
                      </option>
                    </select>
                    <p className="text-xs text-muted-foreground">
                      Choose the appropriate scraper for better extraction
                      accuracy
                    </p>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="edit-window_size">
                      Sliding Window Size
                    </Label>
                    <Input
                      id="edit-window_size"
                      type="number"
                      min="1"
                      max="10"
                      value={newSource.window_size}
                      onChange={(e) =>
                        setNewSource({
                          ...newSource,
                          window_size: parseInt(e.target.value) || 3,
                        })
                      }
                    />
                    <p className="text-xs text-muted-foreground">
                      Number of recent pages to always re-scan (default: 3)
                    </p>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="edit-max_docs">
                      Max Documents per Scrape
                    </Label>
                    <Input
                      id="edit-max_docs"
                      type="number"
                      value={newSource.max_documents}
                      onChange={(e) =>
                        setNewSource({
                          ...newSource,
                          max_documents: e.target.value,
                        })
                      }
                    />
                    <p className="text-xs text-muted-foreground">
                      Default: 1500 documents. Increase for larger scrapes.
                    </p>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="edit-pagination">Enable Pagination</Label>
                    <div className="flex items-center gap-2">
                      <input
                        id="edit-pagination"
                        type="checkbox"
                        checked={newSource.pagination_enabled}
                        onChange={(e) =>
                          setNewSource({
                            ...newSource,
                            pagination_enabled: e.target.checked,
                          })
                        }
                        className="h-4 w-4"
                      />
                      <span className="text-sm">
                        Automatically follow pagination links
                      </span>
                    </div>
                  </div>
                  {newSource.pagination_enabled && (
                    <div className="grid gap-2">
                      <Label htmlFor="edit-max_pages">
                        Max Pages to Scrape
                      </Label>
                      <Input
                        id="edit-max_pages"
                        type="number"
                        value={newSource.max_pages}
                        onChange={(e) =>
                          setNewSource({
                            ...newSource,
                            max_pages: e.target.value,
                          })
                        }
                      />
                      <p className="text-xs text-muted-foreground">
                        Maximum number of pages to follow (default: 100)
                      </p>
                    </div>
                  )}
                </div>
                <DialogFooter>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setIsEditDialogOpen(false);
                      setEditingSource(null);
                      setNewSource({
                        name: "",
                        url: "",
                        description: "",
                        keywords: "",
                        max_documents: 1500,
                        pagination_enabled: true,
                        max_pages: 100,
                        scraper_type: "generic",
                        window_size: 3,
                        force_full_scan: false,
                      });
                    }}
                  >
                    Cancel
                  </Button>
                  <Button onClick={handleUpdateSource}>Update Source</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>

            <Button variant="outline" onClick={handleQuickDemo}>
              <Zap className="mr-2 h-4 w-4" />
              Quick Demo
            </Button>
          </div>

          {/* Sources List */}
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>Scraping Sources</CardTitle>
              <CardDescription>
                Manage websites to scrape for policy documents
              </CardDescription>
            </CardHeader>
            <CardContent>
              {sources.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  <Globe className="mx-auto h-12 w-12 mb-4 opacity-50" />
                  <p>No sources added yet</p>
                  <p className="text-sm">Add a source to start scraping</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {sources.map((source) => (
                    <motion.div
                      key={source.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="border rounded-lg p-4 hover:bg-accent/50 transition-colors"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <h3 className="font-semibold">{source.name}</h3>
                            {source.scraping_enabled ? (
                              <Badge variant="success">
                                <CheckCircle className="mr-1 h-3 w-3" />
                                Enabled
                              </Badge>
                            ) : (
                              <Badge variant="secondary">
                                <Pause className="mr-1 h-3 w-3" />
                                Disabled
                              </Badge>
                            )}
                          </div>
                          <p className="text-sm text-muted-foreground mb-2">
                            {source.url}
                          </p>
                          {source.description && (
                            <p className="text-sm mb-2">{source.description}</p>
                          )}
                          {source.keywords && source.keywords.length > 0 && (
                            <div className="flex items-center gap-2 mb-2 flex-wrap">
                              <span className="text-xs text-muted-foreground">
                                Keywords:
                              </span>
                              {source.keywords.map((keyword, kidx) => (
                                <Badge
                                  key={kidx}
                                  variant="secondary"
                                  className="text-xs"
                                >
                                  {keyword}
                                </Badge>
                              ))}
                            </div>
                          )}
                          <div className="flex items-center gap-4 text-sm text-muted-foreground">
                            <span className="flex items-center gap-1">
                              <FileText className="h-4 w-4" />
                              {source.total_documents_scraped} documents
                            </span>
                            {source.last_scraped_at && (
                              <span className="flex items-center gap-1">
                                <Clock className="h-4 w-4" />
                                Last:{" "}
                                {new Date(
                                  source.last_scraped_at
                                ).toLocaleString()}
                              </span>
                            )}
                            {source.last_scrape_status && (
                              <Badge
                                variant="outline"
                                className={getStatusColor(
                                  source.last_scrape_status
                                )}
                              >
                                {source.last_scrape_status}
                              </Badge>
                            )}
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handlePreview(source.url)}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          {scrapingInProgress[source.id] ? (
                            <>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleStopScraping(source.id)}
                                title="Stop scraping"
                              >
                                <Pause className="h-4 w-4" />
                              </Button>
                              <Button
                                size="sm"
                                disabled
                                title="Scraping in progress..."
                              >
                                <LoadingSpinner className="h-4 w-4" />
                              </Button>
                            </>
                          ) : (
                            <Button
                              size="sm"
                              onClick={() => handleScrapeNow(source.id)}
                              title="Start enhanced scraping"
                            >
                              <Play className="h-4 w-4" />
                            </Button>
                          )}
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleEditSource(source)}
                          >
                            <Pencil className="h-4 w-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="destructive"
                            onClick={() => handleDeleteSource(source.id)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Recent Scrapes */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Recent Scrapes</CardTitle>
                <CardDescription>Latest scraping activity</CardDescription>
              </CardHeader>
              <CardContent>
                {logs.length === 0 ? (
                  <p className="text-center text-muted-foreground py-8">
                    No scraping logs yet
                  </p>
                ) : (
                  <div className="space-y-3">
                    {logs.map((log) => (
                      <div key={log.id} className="border-b pb-3 last:border-0">
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <p className="font-medium text-sm">
                              {log.source_name}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {new Date(log.started_at).toLocaleString()}
                            </p>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge
                              variant={
                                log.status === "success"
                                  ? "success"
                                  : "destructive"
                              }
                            >
                              {log.documents_matched ||
                                log.documents_found ||
                                0}{" "}
                              docs
                            </Badge>
                            {log.status === "success" ? (
                              <CheckCircle className="h-4 w-4 text-green-500" />
                            ) : (
                              <XCircle className="h-4 w-4 text-red-500" />
                            )}
                          </div>
                        </div>
                        {log.keywords_used && log.keywords_used.length > 0 && (
                          <div className="mt-2 flex items-center gap-2 flex-wrap">
                            <span className="text-xs text-muted-foreground">
                              Filtered by:
                            </span>
                            {log.keywords_used.map((keyword, kidx) => (
                              <Badge
                                key={kidx}
                                variant="outline"
                                className="text-xs"
                              >
                                {keyword}
                              </Badge>
                            ))}
                            {log.documents_discovered > 0 && (
                              <span className="text-xs text-muted-foreground">
                                ({log.documents_matched}/
                                {log.documents_discovered} matched)
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Scraped Documents</CardTitle>
                <CardDescription>
                  Recently discovered documents - Click download to save
                </CardDescription>
              </CardHeader>
              <CardContent>
                {scrapedDocs.length > 0 && (
                  <div className="mb-4 space-y-2">
                    {selectedDocs.length > 0 && (
                      <div className="flex items-center gap-2 mb-2">
                        <Button
                          onClick={handleAnalyzeWithAI}
                          className="gap-2"
                          disabled={analyzing}
                        >
                          {analyzing ? (
                            <>
                              <LoadingSpinner className="h-4 w-4" />
                              Analyzing...
                            </>
                          ) : (
                            <>
                              <Zap className="h-4 w-4" />
                              Analyze {selectedDocs.length} Document
                              {selectedDocs.length > 1 ? "s" : ""} with AI
                            </>
                          )}
                        </Button>
                        <Button
                          variant="outline"
                          onClick={() => setSelectedDocs([])}
                          disabled={analyzing}
                        >
                          Clear Selection
                        </Button>
                      </div>
                    )}
                    <Input
                      placeholder="Search documents by keyword (title, source, type)..."
                      value={searchKeyword}
                      onChange={(e) => setSearchKeyword(e.target.value)}
                      className="max-w-md"
                    />
                    {searchKeyword && (
                      <p className="text-sm text-muted-foreground">
                        Showing{" "}
                        {
                          scrapedDocs.filter((doc) => {
                            const keyword = searchKeyword.toLowerCase();
                            return (
                              doc.title?.toLowerCase().includes(keyword) ||
                              doc.source_name
                                ?.toLowerCase()
                                .includes(keyword) ||
                              doc.type?.toLowerCase().includes(keyword)
                            );
                          }).length
                        }{" "}
                        of {scrapedDocs.length} documents
                      </p>
                    )}
                  </div>
                )}
                {scrapedDocs.length === 0 ? (
                  <p className="text-center text-muted-foreground py-8">
                    No documents scraped yet
                  </p>
                ) : (
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {scrapedDocs
                      .filter((doc) => {
                        if (!searchKeyword) return true;
                        const keyword = searchKeyword.toLowerCase();
                        return (
                          doc.title?.toLowerCase().includes(keyword) ||
                          doc.source_name?.toLowerCase().includes(keyword) ||
                          doc.type?.toLowerCase().includes(keyword)
                        );
                      })
                      .map((doc, idx) => (
                        <div
                          key={idx}
                          className="flex items-start gap-3 border-b pb-3 last:border-0"
                        >
                          <input
                            type="checkbox"
                            checked={selectedDocs.some(
                              (d) => d.url === doc.url
                            )}
                            onChange={() => handleToggleDocSelection(doc)}
                            className="mt-1 h-4 w-4 cursor-pointer"
                          />
                          <FileText className="h-5 w-5 text-muted-foreground mt-0.5" />
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-sm truncate">
                              {doc.title}
                            </p>
                            <p className="text-xs text-muted-foreground truncate">
                              {doc.source_url}
                            </p>
                            <div className="flex items-center gap-2 mt-1 flex-wrap">
                              <Badge variant="outline" className="text-xs">
                                {doc.type?.toUpperCase()}
                              </Badge>
                              {doc.provenance?.credibility_score && (
                                <div className="flex items-center gap-1">
                                  <Shield className="h-3 w-3" />
                                  <span className="text-xs">
                                    {doc.provenance.credibility_score}/10
                                  </span>
                                </div>
                              )}
                              {doc.matched_keywords &&
                                doc.matched_keywords.length > 0 && (
                                  <div className="flex items-center gap-1 flex-wrap">
                                    {doc.matched_keywords.map(
                                      (keyword, kidx) => (
                                        <Badge
                                          key={kidx}
                                          variant="secondary"
                                          className="text-xs bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100"
                                        >
                                          {keyword}
                                        </Badge>
                                      )
                                    )}
                                  </div>
                                )}
                            </div>
                          </div>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={async () => {
                              try {
                                // Try to download through our server first
                                const downloadUrl = `${API_BASE_URL}/web-scraping/download-document?url=${encodeURIComponent(
                                  doc.url
                                )}`;

                                // Check if download works
                                const response = await fetch(downloadUrl);

                                if (response.ok) {
                                  // Download through our server
                                  window.open(downloadUrl, "_blank");
                                  toast.success("Download started!");
                                } else {
                                  // Fallback: Open original URL
                                  window.open(doc.url, "_blank");
                                  toast.info("Opening document in new tab");
                                }
                              } catch (error) {
                                // Fallback: Open original URL
                                window.open(doc.url, "_blank");
                                toast.info("Opening document in new tab");
                              }
                            }}
                            title="Download document"
                          >
                            <Download className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Preview Dialog */}
          <Dialog
            open={isPreviewDialogOpen}
            onOpenChange={setIsPreviewDialogOpen}
          >
            <DialogContent className="sm:max-w-[625px]">
              <DialogHeader>
                <DialogTitle>Source Preview</DialogTitle>
                <DialogDescription>
                  Preview of documents available from this source
                </DialogDescription>
              </DialogHeader>
              {!previewData ? (
                <div className="flex justify-center py-8">
                  <LoadingSpinner />
                </div>
              ) : previewData.status === "error" ? (
                <div className="text-center py-8 text-red-500">
                  <AlertCircle className="mx-auto h-12 w-12 mb-4" />
                  <p>Failed to preview source</p>
                  <p className="text-sm">{previewData.error}</p>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Page Title</Label>
                      <p className="text-sm">
                        {previewData.page_title || "N/A"}
                      </p>
                    </div>
                    <div>
                      <Label>Credibility Score</Label>
                      <div className="flex items-center gap-2">
                        <div
                          className={`h-2 w-2 rounded-full ${getCredibilityColor(
                            previewData.source_info?.credibility_score
                          )}`}
                        />
                        <span className="text-sm font-medium">
                          {previewData.source_info?.credibility_score}/10
                        </span>
                        <Badge variant="outline" className="text-xs">
                          {previewData.source_info?.trust_level}
                        </Badge>
                      </div>
                    </div>
                  </div>
                  <div>
                    <Label>
                      Sample Documents ({previewData.sample_documents})
                    </Label>
                    <div className="mt-2 space-y-2 max-h-64 overflow-y-auto">
                      {previewData.documents?.map((doc, idx) => (
                        <div
                          key={idx}
                          className="text-sm p-2 border rounded hover:bg-accent"
                        >
                          <p className="font-medium truncate">{doc.text}</p>
                          <p className="text-xs text-muted-foreground truncate">
                            {doc.url}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
              <DialogFooter>
                <Button onClick={() => setIsPreviewDialogOpen(false)}>
                  Close
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </>
      )}
    </div>
  );
};
