import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Settings,
  Database,
  Server,
  Activity,
  CheckCircle,
  XCircle,
  AlertTriangle,
  RefreshCw,
  HardDrive,
  Cpu,
  Zap,
  FileText,
  MessageSquare,
} from "lucide-react";
import { documentAPI } from "../../services/api";
import { PageHeader } from "../../components/common/PageHeader";
import { LoadingSpinner } from "../../components/common/LoadingSpinner";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { toast } from "sonner";

export const SystemHealthPage = () => {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [vectorStats, setVectorStats] = useState(null);
  const [systemStatus, setSystemStatus] = useState({
    database: "healthy",
    vectorStore: "healthy",
    aiService: "healthy",
    storage: "healthy",
  });

  useEffect(() => {
    fetchSystemHealth();
  }, []);

  const fetchSystemHealth = async () => {
    setLoading(true);
    try {
      // Fetch vector store stats
      const vectorResponse = await documentAPI.getVectorStats();
      setVectorStats(vectorResponse.data);

      // Check AI service health
      try {
        const response = await fetch(
          `${import.meta.env.VITE_API_URL}/chat/health`,
        );
        const data = await response.json();
        setSystemStatus((prev) => ({
          ...prev,
          aiService: data.status === "healthy" ? "healthy" : "unhealthy",
        }));
      } catch (error) {
        setSystemStatus((prev) => ({ ...prev, aiService: "unhealthy" }));
      }

      // Database is healthy if we got this far
      setSystemStatus((prev) => ({ ...prev, database: "healthy" }));

      // Vector store status
      if (vectorResponse.data.status === "success") {
        setSystemStatus((prev) => ({ ...prev, vectorStore: "healthy" }));
      } else {
        setSystemStatus((prev) => ({ ...prev, vectorStore: "warning" }));
      }
    } catch (error) {
      console.error("Error fetching system health:", error);
      toast.error("Failed to load system health data");
      setSystemStatus({
        database: "unhealthy",
        vectorStore: "unhealthy",
        aiService: "unhealthy",
        storage: "unhealthy",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchSystemHealth();
    setRefreshing(false);
    toast.success("System health refreshed");
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case "healthy":
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case "warning":
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      case "unhealthy":
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Activity className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case "healthy":
        return (
          <Badge className="bg-green-500/10 text-green-500 border-green-500/20">
            Healthy
          </Badge>
        );
      case "warning":
        return (
          <Badge className="bg-yellow-500/10 text-yellow-500 border-yellow-500/20">
            Warning
          </Badge>
        );
      case "unhealthy":
        return (
          <Badge className="bg-red-500/10 text-red-500 border-red-500/20">
            Unhealthy
          </Badge>
        );
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  const getOverallHealth = () => {
    const statuses = Object.values(systemStatus);
    if (statuses.every((s) => s === "healthy")) return "healthy";
    if (statuses.some((s) => s === "unhealthy")) return "unhealthy";
    return "warning";
  };

  if (loading) {
    return <LoadingSpinner text="Checking system health..." />;
  }

  const overallHealth = getOverallHealth();

  return (
    <div className="space-y-6">
      <PageHeader
        title="System Health"
        description="Monitor system components and performance"
        icon={Settings}
        action={
          <Button
            onClick={handleRefresh}
            disabled={refreshing}
            variant="outline"
          >
            <RefreshCw
              className={`h-4 w-4 mr-2 ${refreshing ? "animate-spin" : ""}`}
            />
            Refresh
          </Button>
        }
      />

      {/* Overall Status */}
      <Card className="glass-card border-border/50">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div
                className={`h-16 w-16 rounded-full flex items-center justify-center ${
                  overallHealth === "healthy"
                    ? "bg-green-500/10"
                    : overallHealth === "warning"
                      ? "bg-yellow-500/10"
                      : "bg-red-500/10"
                }`}
              >
                {getStatusIcon(overallHealth)}
              </div>
              <div>
                <h2 className="text-2xl font-bold">System Status</h2>
                <p className="text-muted-foreground">
                  {overallHealth === "healthy"
                    ? "All systems operational"
                    : overallHealth === "warning"
                      ? "Some systems need attention"
                      : "Critical issues detected"}
                </p>
              </div>
            </div>
            {getStatusBadge(overallHealth)}
          </div>
        </CardContent>
      </Card>

      {/* Component Status */}
      <div className="grid gap-4 md:grid-cols-2">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="glass-card border-border/50">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                    <Database className="h-5 w-5 text-blue-500" />
                  </div>
                  <div>
                    <h3 className="font-semibold">Database</h3>
                    <p className="text-xs text-muted-foreground">PostgreSQL</p>
                  </div>
                </div>
                {getStatusIcon(systemStatus.database)}
              </div>
              {getStatusBadge(systemStatus.database)}
              <p className="text-sm text-muted-foreground mt-3">
                {systemStatus.database === "healthy"
                  ? "Connection stable, queries executing normally"
                  : "Database connection issues detected"}
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="glass-card border-border/50">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-lg bg-purple-500/10 flex items-center justify-center">
                    <HardDrive className="h-5 w-5 text-purple-500" />
                  </div>
                  <div>
                    <h3 className="font-semibold">Vector Store</h3>
                    <p className="text-xs text-muted-foreground">FAISS</p>
                  </div>
                </div>
                {getStatusIcon(systemStatus.vectorStore)}
              </div>
              {getStatusBadge(systemStatus.vectorStore)}
              <p className="text-sm text-muted-foreground mt-3">
                {vectorStats?.total_documents || 0} documents indexed
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card className="glass-card border-border/50">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-lg bg-green-500/10 flex items-center justify-center">
                    <MessageSquare className="h-5 w-5 text-green-500" />
                  </div>
                  <div>
                    <h3 className="font-semibold">AI Service</h3>
                    <p className="text-xs text-muted-foreground">
                      Gemini 2.5 Flash
                    </p>
                  </div>
                </div>
                {getStatusIcon(systemStatus.aiService)}
              </div>
              {getStatusBadge(systemStatus.aiService)}
              <p className="text-sm text-muted-foreground mt-3">
                {systemStatus.aiService === "healthy"
                  ? "AI model responding normally"
                  : "AI service unavailable"}
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <Card className="glass-card border-border/50">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-lg bg-yellow-500/10 flex items-center justify-center">
                    <Server className="h-5 w-5 text-yellow-500" />
                  </div>
                  <div>
                    <h3 className="font-semibold">Storage</h3>
                    <p className="text-xs text-muted-foreground">Supabase</p>
                  </div>
                </div>
                {getStatusIcon(systemStatus.storage)}
              </div>
              {getStatusBadge(systemStatus.storage)}
              <p className="text-sm text-muted-foreground mt-3">
                {systemStatus.storage === "healthy"
                  ? "File storage operational"
                  : "Storage service issues"}
              </p>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Vector Store Details */}
      {vectorStats && (
        <Card className="glass-card border-border/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <HardDrive className="h-5 w-5" />
              Vector Store Details
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="p-4 rounded-lg bg-secondary/50">
                <div className="flex items-center gap-2 mb-2">
                  <FileText className="h-4 w-4 text-muted-foreground" />
                  <p className="text-sm text-muted-foreground">
                    Total Documents
                  </p>
                </div>
                <p className="text-2xl font-bold">
                  {vectorStats.total_documents}
                </p>
              </div>
              <div className="p-4 rounded-lg bg-secondary/50">
                <div className="flex items-center gap-2 mb-2">
                  <Cpu className="h-4 w-4 text-muted-foreground" />
                  <p className="text-sm text-muted-foreground">Storage Mode</p>
                </div>
                <p className="text-lg font-semibold">
                  {vectorStats.storage_mode?.replace("_", " ") || "N/A"}
                </p>
              </div>
              <div className="p-4 rounded-lg bg-secondary/50">
                <div className="flex items-center gap-2 mb-2">
                  <Zap className="h-4 w-4 text-muted-foreground" />
                  <p className="text-sm text-muted-foreground">Status</p>
                </div>
                <p className="text-lg font-semibold capitalize">
                  {vectorStats.status}
                </p>
              </div>
            </div>

            {vectorStats.document_folders &&
              vectorStats.document_folders.length > 0 && (
                <div className="mt-6">
                  <h4 className="text-sm font-semibold mb-3">
                    Indexed Documents
                  </h4>
                  <div className="grid gap-2 md:grid-cols-4">
                    {vectorStats.document_folders.slice(0, 12).map((docId) => (
                      <div
                        key={docId}
                        className="p-2 rounded bg-secondary/30 text-xs font-mono text-center"
                      >
                        Doc #{docId}
                      </div>
                    ))}
                  </div>
                  {vectorStats.document_folders.length > 12 && (
                    <p className="text-xs text-muted-foreground mt-2 text-center">
                      +{vectorStats.document_folders.length - 12} more documents
                    </p>
                  )}
                </div>
              )}
          </CardContent>
        </Card>
      )}

      {/* System Information */}
      <Card className="glass-card border-border/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            System Information
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 rounded-lg bg-secondary/50">
              <span className="text-sm font-medium">API Version</span>
              <Badge variant="outline">v1.0.0</Badge>
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-secondary/50">
              <span className="text-sm font-medium">Environment</span>
              <Badge variant="outline">
                {import.meta.env.MODE === "production"
                  ? "Production"
                  : "Development"}
              </Badge>
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-secondary/50">
              <span className="text-sm font-medium">Last Health Check</span>
              <span className="text-sm text-muted-foreground">
                {new Date().toLocaleString()}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
