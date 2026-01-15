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
  GitBranch,
  Users,
  Database,
  RefreshCw,
  Filter,
  Search,
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
import api from "../../services/api";

export const EnhancedWebScrapingPage = () => {
  const [loading, setLoading] = useState(true);
  const [sources, setSources] = useState([]);
  const [stats, setStats] = useState(null);
  const [logs, setLogs] = useState([]);
  const [scrapedDocs, setScrapedDocs] = useState([]);
  const [documentFamilies, setDocumentFamilies] = useState([]);
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isPreviewDialogOpen, setIsPreviewDialogOpen] = useState(false);
  const [isFamilyDialogOpen, setIsFamilyDialogOpen] = useState(false);
  const [previewData, setPreviewData] = useState(null);
  const [selectedFamily, setSelectedFamily] = useState(null);
  const [scrapingInProgress, setScrapingInProgress] = useState({});
  const [searchKeyword, setSearchKeyword] = useState("");
  const [familyFilter, setFamilyFilter] = useState("");
  const [editingSource, setEditingSource] = useState(null);
  const [selectedDocs, setSelectedDocs] = useState([]);
  const [analyzing, setAnalyzing] = useState(false);

  // Form state
  const [newSource, setNewSource] = useState({
    name: "",
    url: "",
    description: "",
    keywords: "",
    max_documents: 1500,
    pagination_enabled: true,
    max_pages: 100,
    incremental: true, // New: enable incremental scraping
  });

  // View state
  const [activeView, setActiveView] = useState("sources"); // "sources", "logs", "families"

  const navigate = useNavigate();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [sourcesRes, statsRes, logsRes, docsRes, familiesRes] =
        await Promise.all([
          api.get("/api/web-scraping/sources"),
          api.get("/api/enhanced-web-scraping/stats-enhanced"), // Enhanced stats
          api.get("/api/web-scraping/logs?limit=10"),
          api.get("/api/web-scraping/scraped-documents?limit=1000"),
          api.get("/api/enhanced-web-scraping/document-families?limit=100"), // New: fetch families
        ]);

      setSources(sourcesRes.data);
      setStats(statsRes.data);
      setLogs(logsRes.data);
      setScrapedDocs(docsRes.data);
      setDocumentFamilies(familiesRes.data);
    } catch (error) {
      console.error("Error fetching data:", error);
      toast.error("Failed to load web scraping data");
    } finally {
      setLoading(false);
    }
  };

  const handleEnhancedScrape = async (sourceId) => {
    try {
      setScrapingInProgress((prev) => ({ ...prev, [sourceId]: true }));
      toast.info("Starting enhanced scraping with family management...");

      const source = sources.find((s) => s.id === sourceId);

      // Use enhanced scraping endpoint
      const response = await api.post(
        "/api/enhanced-web-scraping/scrape-enhanced",
        {
          source_id: sourceId,
          keywords: source?.keywords || null,
          max_documents: source?.max_documents || 1500,
          pagination_enabled: source?.pagination_enabled !== false,
          max_pages: source?.max_pages || 100,
          incremental: newSource.incremental, // Use incremental scraping
        }
      );

      const result = response.data;

      // Show detailed results
      const successMsg = `Enhanced scraping complete!`;
      const details = [
        `📄 New: ${result.documents_new || 0}`,
        `🔄 Updated: ${result.documents_updated || 0}`,
        `📁 Families created: ${result.families_created || 0}`,
        `🔗 Families updated: ${result.families_updated || 0}`,
        `⏭️ Unchanged: ${result.documents_unchanged || 0}`,
        `🔄 Duplicates: ${result.documents_duplicate || 0}`,
      ].join(" | ");

      toast.success(successMsg, {
        description: details,
        duration: 5000,
      });

      // Refresh data
      setTimeout(() => {
        fetchData();
      }, 500);
    } catch (error) {
      console.error("Error in enhanced scraping:", error);
      toast.error(error.response?.data?.detail || "Enhanced scraping failed");
    } finally {
      setScrapingInProgress((prev) => ({ ...prev, [sourceId]: false }));
    }
  };

  const handleViewFamily = async (familyId) => {
    try {
      const response = await api.get(
        `/api/enhanced-web-scraping/document-families/${familyId}/evolution`
      );
      setSelectedFamily(response.data);
      setIsFamilyDialogOpen(true);
    } catch (error) {
      console.error("Error fetching family details:", error);
      toast.error("Failed to load family details");
    }
  };

  const handleMigrateFamilies = async () => {
    try {
      toast.info("Starting document family migration...");

      const response = await api.post(
        "/api/enhanced-web-scraping/document-families/migrate-existing"
      );

      toast.success("Family migration completed!", {
        description: `Processed ${response.data.total_documents} documents into ${response.data.total_families} families`,
        duration: 5000,
      });

      fetchData();
    } catch (error) {
      console.error("Error migrating families:", error);
      toast.error("Family migration failed");
    }
  };

  const getVersionBadgeColor = (isLatest) => {
    return isLatest ? "bg-green-500" : "bg-gray-500";
  };

  const getFamilyStatusColor = (status) => {
    switch (status) {
      case "active":
        return "bg-green-500";
      case "archived":
        return "bg-gray-500";
      default:
        return "bg-blue-500";
    }
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
        title="Enhanced Web Scraping"
        description="Intelligent document ingestion with family management and deduplication"
        icon={Globe}
      />

      {/* Enhanced Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Document Families
              </CardTitle>
              <GitBranch className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {stats?.total_families || 0}
              </div>
              <p className="text-xs text-muted-foreground">
                {stats?.avg_docs_per_family || 0} avg docs/family
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
                Latest Versions
              </CardTitle>
              <RefreshCw className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {stats?.latest_versions || 0}
              </div>
              <p className="text-xs text-muted-foreground">
                {stats?.total_versions || 0} total versions
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
                Deduplication Rate
              </CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {stats?.deduplication_rate
                  ? `${stats.deduplication_rate}%`
                  : "0%"}
              </div>
              <p className="text-xs text-muted-foreground">
                {stats?.duplicates_found || 0} duplicates found
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
                Update Detection
              </CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {stats?.updates_detected || 0}
              </div>
              <p className="text-xs text-muted-foreground">
                {stats?.incremental_scrapes || 0} incremental scrapes
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                RAG Accuracy
              </CardTitle>
              <Zap className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {stats?.rag_accuracy ? `${stats.rag_accuracy}%` : "N/A"}
              </div>
              <p className="text-xs text-muted-foreground">
                Family-aware retrieval
              </p>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Enhanced View Toggle */}
      <div className="flex gap-2 mb-6">
        <Button
          variant={activeView === "sources" ? "default" : "outline"}
          onClick={() => setActiveView("sources")}
        >
          <Settings className="mr-2 h-4 w-4" />
          Sources & Scraping
        </Button>
        <Button
          variant={activeView === "families" ? "default" : "outline"}
          onClick={() => setActiveView("families")}
        >
          <GitBranch className="mr-2 h-4 w-4" />
          Document Families
        </Button>
        <Button
          variant={activeView === "logs" ? "default" : "outline"}
          onClick={() => setActiveView("logs")}
        >
          <Activity className="mr-2 h-4 w-4" />
          Scraping Logs
        </Button>
      </div>

      {/* Document Families View */}
      {activeView === "families" && (
        <div className="space-y-6">
          {/* Family Management Actions */}
          <div className="flex gap-4 mb-6">
            <Button onClick={handleMigrateFamilies}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Migrate Existing Documents
            </Button>
            <div className="flex-1 max-w-md">
              <Input
                placeholder="Filter families by title, category, or ministry..."
                value={familyFilter}
                onChange={(e) => setFamilyFilter(e.target.value)}
              />
            </div>
          </div>

          {/* Document Families List */}
          <Card>
            <CardHeader>
              <CardTitle>Document Families</CardTitle>
              <CardDescription>
                Grouped documents with version management and deduplication
              </CardDescription>
            </CardHeader>
            <CardContent>
              {documentFamilies.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  <GitBranch className="mx-auto h-12 w-12 mb-4 opacity-50" />
                  <p>No document families found</p>
                  <p className="text-sm">
                    Run migration to create families from existing documents
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {documentFamilies
                    .filter((family) => {
                      if (!familyFilter) return true;
                      const filter = familyFilter.toLowerCase();
                      return (
                        family.canonical_title
                          ?.toLowerCase()
                          .includes(filter) ||
                        family.category?.toLowerCase().includes(filter) ||
                        family.ministry?.toLowerCase().includes(filter)
                      );
                    })
                    .map((family) => (
                      <motion.div
                        key={family.id}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="border rounded-lg p-4 hover:bg-accent/50 transition-colors"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <h3 className="font-semibold">
                                {family.canonical_title}
                              </h3>
                              <Badge variant="outline">
                                {family.document_count} versions
                              </Badge>
                              {family.category && (
                                <Badge variant="secondary">
                                  {family.category}
                                </Badge>
                              )}
                            </div>

                            {family.ministry && (
                              <p className="text-sm text-muted-foreground mb-2">
                                {family.ministry}
                              </p>
                            )}

                            <div className="flex items-center gap-4 text-sm text-muted-foreground">
                              <span className="flex items-center gap-1">
                                <FileText className="h-4 w-4" />
                                Latest: v{family.latest_version}
                              </span>
                              <span className="flex items-center gap-1">
                                <Clock className="h-4 w-4" />
                                Updated:{" "}
                                {new Date(
                                  family.updated_at
                                ).toLocaleDateString()}
                              </span>
                            </div>
                          </div>

                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleViewFamily(family.id)}
                            >
                              <Eye className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      </motion.div>
                    ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Sources View (Enhanced) */}
      {activeView === "sources" && (
        <div className="space-y-6">
          {/* Enhanced Action Buttons */}
          <div className="flex gap-4 mb-6">
            <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  Add Enhanced Source
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[625px]">
                <DialogHeader>
                  <DialogTitle>Add Enhanced Web Scraping Source</DialogTitle>
                  <DialogDescription>
                    Add a source with family management and deduplication
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  {/* Same form fields as before, plus: */}
                  <div className="grid gap-2">
                    <Label htmlFor="incremental">
                      Enable Incremental Scraping
                    </Label>
                    <div className="flex items-center gap-2">
                      <input
                        id="incremental"
                        type="checkbox"
                        checked={newSource.incremental}
                        onChange={(e) =>
                          setNewSource({
                            ...newSource,
                            incremental: e.target.checked,
                          })
                        }
                        className="h-4 w-4"
                      />
                      <span className="text-sm">
                        Skip unchanged documents and detect updates
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Recommended: Reduces duplicate processing and detects
                      document updates
                    </p>
                  </div>
                  {/* ... other form fields ... */}
                </div>
                <DialogFooter>
                  <Button
                    variant="outline"
                    onClick={() => setIsAddDialogOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={() => {
                      /* handleAddSource with enhanced features */
                    }}
                  >
                    Add Enhanced Source
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>

            <Button
              variant="outline"
              onClick={() => {
                /* handleQuickDemo with families */
              }}
            >
              <Zap className="mr-2 h-4 w-4" />
              Enhanced Demo
            </Button>
          </div>

          {/* Enhanced Sources List */}
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>Enhanced Scraping Sources</CardTitle>
              <CardDescription>
                Sources with family management, deduplication, and update
                detection
              </CardDescription>
            </CardHeader>
            <CardContent>
              {sources.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  <Globe className="mx-auto h-12 w-12 mb-4 opacity-50" />
                  <p>No sources added yet</p>
                  <p className="text-sm">
                    Add an enhanced source to start intelligent scraping
                  </p>
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
                                Enhanced
                              </Badge>
                            ) : (
                              <Badge variant="secondary">
                                <Pause className="mr-1 h-3 w-3" />
                                Disabled
                              </Badge>
                            )}
                            <Badge variant="outline">
                              <GitBranch className="mr-1 h-3 w-3" />
                              {source.families_created || 0} families
                            </Badge>
                          </div>

                          {/* Enhanced stats */}
                          <div className="flex items-center gap-4 text-sm text-muted-foreground mb-2">
                            <span>
                              📄 {source.total_documents_scraped} docs
                            </span>
                            <span>
                              🔄 {source.updates_detected || 0} updates
                            </span>
                            <span>
                              🔗 {source.duplicates_skipped || 0} duplicates
                            </span>
                          </div>

                          {/* ... rest of source display ... */}
                        </div>

                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            onClick={() => handleEnhancedScrape(source.id)}
                            disabled={scrapingInProgress[source.id]}
                          >
                            {scrapingInProgress[source.id] ? (
                              <LoadingSpinner className="h-4 w-4" />
                            ) : (
                              <>
                                <Zap className="h-4 w-4 mr-1" />
                                Enhanced
                              </>
                            )}
                          </Button>
                          {/* ... other buttons ... */}
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Logs View */}
      {activeView === "logs" && <ScrapingLogs />}

      {/* Family Details Dialog */}
      <Dialog open={isFamilyDialogOpen} onOpenChange={setIsFamilyDialogOpen}>
        <DialogContent className="sm:max-w-[800px]">
          <DialogHeader>
            <DialogTitle>Document Family Evolution</DialogTitle>
            <DialogDescription>
              Version history and relationships for this document family
            </DialogDescription>
          </DialogHeader>
          {selectedFamily && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Family Title</Label>
                  <p className="text-sm font-medium">
                    {selectedFamily.canonical_title}
                  </p>
                </div>
                <div>
                  <Label>Category</Label>
                  <p className="text-sm">{selectedFamily.category}</p>
                </div>
              </div>

              <div>
                <Label>
                  Version History ({selectedFamily.versions?.length || 0}{" "}
                  versions)
                </Label>
                <div className="mt-2 space-y-2 max-h-64 overflow-y-auto">
                  {selectedFamily.versions?.map((version, idx) => (
                    <div
                      key={version.document_id}
                      className="text-sm p-3 border rounded hover:bg-accent"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium">
                          v{version.version_number}
                        </span>
                        <div className="flex gap-2">
                          {version.is_latest_version && (
                            <Badge variant="success" className="text-xs">
                              Latest
                            </Badge>
                          )}
                          <Badge variant="outline" className="text-xs">
                            {version.approval_status}
                          </Badge>
                        </div>
                      </div>
                      <p className="text-muted-foreground truncate">
                        {version.title}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(version.uploaded_at).toLocaleString()}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button onClick={() => setIsFamilyDialogOpen(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};
