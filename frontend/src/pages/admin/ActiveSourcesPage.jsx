import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Database,
  RefreshCw,
  CheckCircle,
  XCircle,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Clock,
  Building2,
  User,
  Calendar,
  FileText,
  Loader2,
} from "lucide-react";
import { dataSourceAPI } from "../../services/api";
import { PageHeader } from "../../components/common/PageHeader";
import { LoadingSpinner } from "../../components/common/LoadingSpinner";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../../components/ui/table";
import { Alert, AlertDescription } from "../../components/ui/alert";
import { formatDateTime } from "../../utils/dateFormat";
import { toast } from "sonner";
import { formatErrorForToast } from "../../utils/errorHandlers";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "../../components/ui/collapsible";

export const ActiveSourcesPage = () => {
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [expandedRows, setExpandedRows] = useState(new Set());
  const [syncLogs, setSyncLogs] = useState({});
  const [loadingLogs, setLoadingLogs] = useState({});
  const [triggeringSync, setTriggeringSync] = useState({});

  useEffect(() => {
    fetchActiveSources();
  }, []);

  const fetchActiveSources = async (isRefresh = false) => {
    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    try {
      const response = await dataSourceAPI.activeSources();
      setSources(response.data.sources || []);
      if (isRefresh) {
        toast.success("✅ Sources refreshed");
      }
    } catch (error) {
      console.error("Error fetching active sources:", error);
      toast.error(formatErrorForToast(error, "Failed to load active sources"));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const fetchSyncLogs = async (sourceId) => {
    if (syncLogs[sourceId]) {
      // Already loaded
      return;
    }

    setLoadingLogs((prev) => ({ ...prev, [sourceId]: true }));
    try {
      const response = await dataSourceAPI.syncLogs(sourceId, 5);
      setSyncLogs((prev) => ({
        ...prev,
        [sourceId]: response.data.logs || [],
      }));
    } catch (error) {
      console.error("Error fetching sync logs:", error);
      toast.error(formatErrorForToast(error, "Failed to load sync logs"));
    } finally {
      setLoadingLogs((prev) => ({ ...prev, [sourceId]: false }));
    }
  };

  const toggleRow = (sourceId) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(sourceId)) {
      newExpanded.delete(sourceId);
    } else {
      newExpanded.add(sourceId);
      fetchSyncLogs(sourceId);
    }
    setExpandedRows(newExpanded);
  };

  const getStatusBadge = (status) => {
    const variants = {
      approved: {
        variant: "default",
        icon: CheckCircle,
        color: "text-green-500",
        label: "Approved",
      },
      active: {
        variant: "default",
        icon: CheckCircle,
        color: "text-blue-500",
        label: "Active",
      },
      failed: {
        variant: "destructive",
        icon: XCircle,
        color: "text-red-500",
        label: "Failed",
      },
    };

    const config = variants[status] || variants.approved;
    const Icon = config.icon;

    return (
      <Badge variant={config.variant} className="gap-1">
        <Icon className={`h-3 w-3 ${config.color}`} />
        {config.label}
      </Badge>
    );
  };

  const getSyncStatusBadge = (syncStatus) => {
    if (!syncStatus) {
      return (
        <Badge variant="outline" className="gap-1">
          <Clock className="h-3 w-3 text-gray-500" />
          Not Synced
        </Badge>
      );
    }

    const variants = {
      success: {
        variant: "default",
        icon: CheckCircle,
        color: "text-green-500",
        label: "Success",
      },
      failed: {
        variant: "destructive",
        icon: XCircle,
        color: "text-red-500",
        label: "Failed",
      },
      in_progress: {
        variant: "outline",
        icon: RefreshCw,
        color: "text-blue-500 animate-spin",
        label: "In Progress",
      },
    };

    const config = variants[syncStatus] || variants.success;
    const Icon = config.icon;

    return (
      <Badge variant={config.variant} className="gap-1">
        <Icon className={`h-3 w-3 ${config.color}`} />
        {config.label}
      </Badge>
    );
  };

  const getClassificationBadge = (classification) => {
    const colors = {
      public: "bg-blue-500/10 text-blue-500",
      educational: "bg-purple-500/10 text-purple-500",
      confidential: "bg-red-500/10 text-red-500",
      institutional: "bg-green-500/10 text-green-500",
    };

    return (
      <Badge className={colors[classification] || ""}>
        {classification?.charAt(0).toUpperCase() + classification?.slice(1)}
      </Badge>
    );
  };

  const handleTriggerSync = async (sourceId, sourceName) => {
    setTriggeringSync((prev) => ({ ...prev, [sourceId]: true }));
    try {
      await dataSourceAPI.triggerSync(sourceId);
      toast.success(`✅ Sync started for ${sourceName}`);
      // Refresh after a short delay
      setTimeout(() => fetchActiveSources(false), 2000);
    } catch (error) {
      console.error("Error triggering sync:", error);
      toast.error(formatErrorForToast(error, "Failed to trigger sync"));
    } finally {
      setTriggeringSync((prev) => ({ ...prev, [sourceId]: false }));
    }
  };

  if (loading) {
    return <LoadingSpinner text="Loading active sources..." />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <PageHeader
          title="Active Data Sources"
          description="Monitor all approved and active external data sources"
          icon={Database}
        />
        <Button
          onClick={() => fetchActiveSources(true)}
          variant="outline"
          disabled={refreshing}
        >
          <RefreshCw
            className={`h-4 w-4 mr-2 ${refreshing ? "animate-spin" : ""}`}
          />
          {refreshing ? "Refreshing..." : "Refresh"}
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="glass-card border-border/50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Active
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{sources.length}</div>
          </CardContent>
        </Card>

        <Card className="glass-card border-border/50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Syncing Successfully
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-500">
              {sources.filter((s) => s.last_sync_status === "success").length}
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card border-border/50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Failed Syncs
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-500">
              {
                sources.filter(
                  (s) =>
                    s.last_sync_status === "failed" ||
                    s.request_status === "failed"
                ).length
              }
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card border-border/50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Documents
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {sources.reduce(
                (sum, s) => sum + (s.total_documents_synced || 0),
                0
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {sources.length === 0 ? (
        <Card className="glass-card border-border/50">
          <CardContent className="p-6 sm:p-12 text-center">
            <Database className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
            <h3 className="text-lg font-semibold mb-2">No Active Sources</h3>
            <p className="text-sm sm:text-base text-muted-foreground">
              There are no approved or active data sources yet.
            </p>
          </CardContent>
        </Card>
      ) : (
        <Card className="glass-card border-border/50">
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12"></TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Institution</TableHead>
                    <TableHead>Database</TableHead>
                    <TableHead>Classification</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Last Sync</TableHead>
                    <TableHead>Sync Status</TableHead>
                    <TableHead>Documents</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sources.map((source, index) => (
                    <React.Fragment key={source.id}>
                      <motion.tr
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.05 }}
                        className="border-border/40"
                      >
                        <TableCell>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => toggleRow(source.id)}
                          >
                            {expandedRows.has(source.id) ? (
                              <ChevronUp className="h-4 w-4" />
                            ) : (
                              <ChevronDown className="h-4 w-4" />
                            )}
                          </Button>
                        </TableCell>
                        <TableCell className="font-medium">
                          <div>
                            <div>{source.name}</div>
                            {source.description && (
                              <div className="text-xs text-muted-foreground mt-1">
                                {source.description}
                              </div>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Building2 className="h-4 w-4 text-muted-foreground" />
                            <div>
                              <div className="text-sm">
                                {source.institution?.name || "N/A"}
                              </div>
                              <div className="text-xs text-muted-foreground">
                                {source.institution?.type || ""}
                              </div>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="text-sm">
                            <div className="font-medium">
                              {source.db_type?.toUpperCase() || "PostgreSQL"}
                            </div>
                            <div className="text-xs text-muted-foreground">
                              {source.host}:{source.port}
                            </div>
                            <div className="text-xs text-muted-foreground">
                              {source.database_name}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          {getClassificationBadge(source.data_classification)}
                        </TableCell>
                        <TableCell>
                          {getStatusBadge(source.request_status)}
                        </TableCell>
                        <TableCell className="text-sm">
                          {source.last_sync_at ? (
                            <div className="flex items-center gap-1">
                              <Clock className="h-3 w-3 text-muted-foreground" />
                              {formatDateTime(source.last_sync_at)}
                            </div>
                          ) : (
                            <span className="text-muted-foreground">Never</span>
                          )}
                        </TableCell>
                        <TableCell>
                          {getSyncStatusBadge(source.last_sync_status)}
                        </TableCell>
                        <TableCell className="text-sm font-medium">
                          {source.total_documents_synced || 0}
                        </TableCell>
                        <TableCell>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() =>
                              handleTriggerSync(source.id, source.name)
                            }
                            disabled={triggeringSync[source.id]}
                          >
                            <RefreshCw
                              className={`h-3 w-3 mr-1 ${
                                triggeringSync[source.id] ? "animate-spin" : ""
                              }`}
                            />
                            {triggeringSync[source.id] ? "Syncing..." : "Sync"}
                          </Button>
                        </TableCell>
                      </motion.tr>

                      {/* Expandable Details Row */}
                      {expandedRows.has(source.id) && (
                        <motion.tr
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          className="border-border/40 bg-muted/20"
                        >
                          <TableCell colSpan={10} className="p-6">
                            <div className="space-y-4">
                              {/* Source Details */}
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                  <h4 className="text-sm font-semibold mb-2 flex items-center gap-2">
                                    <User className="h-4 w-4" />
                                    Request Details
                                  </h4>
                                  <div className="space-y-1 text-sm">
                                    <div>
                                      <span className="text-muted-foreground">
                                        Requested by:
                                      </span>{" "}
                                      {source.requested_by?.name || "N/A"}
                                    </div>
                                    <div>
                                      <span className="text-muted-foreground">
                                        Requested at:
                                      </span>{" "}
                                      {formatDateTime(source.requested_at)}
                                    </div>
                                    <div>
                                      <span className="text-muted-foreground">
                                        Approved by:
                                      </span>{" "}
                                      {source.approved_by?.name || "N/A"}
                                    </div>
                                    <div>
                                      <span className="text-muted-foreground">
                                        Approved at:
                                      </span>{" "}
                                      {formatDateTime(source.approved_at)}
                                    </div>
                                  </div>
                                </div>

                                <div>
                                  <h4 className="text-sm font-semibold mb-2 flex items-center gap-2">
                                    <Database className="h-4 w-4" />
                                    Database Details
                                  </h4>
                                  <div className="space-y-1 text-sm">
                                    <div>
                                      <span className="text-muted-foreground">
                                        Table:
                                      </span>{" "}
                                      {source.table_name}
                                    </div>
                                    <div>
                                      <span className="text-muted-foreground">
                                        Sync Enabled:
                                      </span>{" "}
                                      {source.sync_enabled ? "Yes" : "No"}
                                    </div>
                                  </div>
                                </div>
                              </div>

                              {/* Sync Error Message */}
                              {source.last_sync_message &&
                                source.last_sync_status === "failed" && (
                                  <Alert variant="destructive">
                                    <AlertTriangle className="h-4 w-4" />
                                    <AlertDescription>
                                      <strong>Sync Error:</strong>{" "}
                                      {source.last_sync_message}
                                    </AlertDescription>
                                  </Alert>
                                )}

                              {/* Sync Logs */}
                              <div>
                                <h4 className="text-sm font-semibold mb-2 flex items-center gap-2">
                                  <FileText className="h-4 w-4" />
                                  Recent Sync Logs
                                </h4>
                                {loadingLogs[source.id] ? (
                                  <div className="text-sm text-muted-foreground">
                                    Loading logs...
                                  </div>
                                ) : syncLogs[source.id]?.length > 0 ? (
                                  <div className="space-y-2">
                                    {syncLogs[source.id].map((log) => (
                                      <div
                                        key={log.id}
                                        className="p-3 rounded-lg border border-border/50 bg-background/50"
                                      >
                                        <div className="flex items-center justify-between mb-2">
                                          <div className="flex items-center gap-2">
                                            {getSyncStatusBadge(log.status)}
                                            <span className="text-xs text-muted-foreground">
                                              {formatDateTime(log.started_at)}
                                            </span>
                                          </div>
                                          {log.sync_duration_seconds && (
                                            <span className="text-xs text-muted-foreground">
                                              Duration:{" "}
                                              {log.sync_duration_seconds}s
                                            </span>
                                          )}
                                        </div>
                                        <div className="grid grid-cols-3 gap-2 text-xs">
                                          <div>
                                            <span className="text-muted-foreground">
                                              Fetched:
                                            </span>{" "}
                                            {log.documents_fetched || 0}
                                          </div>
                                          <div>
                                            <span className="text-muted-foreground">
                                              Processed:
                                            </span>{" "}
                                            {log.documents_processed || 0}
                                          </div>
                                          <div>
                                            <span className="text-muted-foreground">
                                              Failed:
                                            </span>{" "}
                                            {log.documents_failed || 0}
                                          </div>
                                        </div>
                                        {log.error_message && (
                                          <div className="mt-2 text-xs text-red-500">
                                            Error: {log.error_message}
                                          </div>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                ) : (
                                  <div className="text-sm text-muted-foreground">
                                    No sync logs available
                                  </div>
                                )}
                              </div>
                            </div>
                          </TableCell>
                        </motion.tr>
                      )}
                    </React.Fragment>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
