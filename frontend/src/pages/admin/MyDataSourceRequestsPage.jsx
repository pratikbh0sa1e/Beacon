import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Database,
  Clock,
  CheckCircle,
  XCircle,
  RefreshCw,
  Loader2,
} from "lucide-react";
import { dataSourceAPI } from "../../services/api";
import { PageHeader } from "../../components/common/PageHeader";
import { LoadingSpinner } from "../../components/common/LoadingSpinner";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { Card, CardContent } from "../../components/ui/card";
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

export const MyDataSourceRequestsPage = () => {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchRequests();
  }, []);

  const fetchRequests = async (isRefresh = false) => {
    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    try {
      const response = await dataSourceAPI.myRequests();
      setRequests(response.data.requests || []);
      if (isRefresh) {
        toast.success("✅ Requests refreshed");
      }
    } catch (error) {
      console.error("Error fetching requests:", error);
      toast.error(formatErrorForToast(error, "Failed to load requests"));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const getStatusBadge = (status) => {
    const variants = {
      pending: { variant: "outline", icon: Clock, color: "text-yellow-500" },
      approved: {
        variant: "default",
        icon: CheckCircle,
        color: "text-green-500",
      },
      rejected: {
        variant: "destructive",
        icon: XCircle,
        color: "text-red-500",
      },
      active: {
        variant: "default",
        icon: CheckCircle,
        color: "text-blue-500",
      },
      failed: {
        variant: "destructive",
        icon: XCircle,
        color: "text-orange-500",
      },
    };

    const config = variants[status] || variants.pending;
    const Icon = config.icon;

    return (
      <Badge variant={config.variant} className="gap-1">
        <Icon className={`h-3 w-3 ${config.color}`} />
        {status.charAt(0).toUpperCase() + status.slice(1)}
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

  if (loading) {
    return <LoadingSpinner text="Loading requests..." />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <PageHeader
          title="My Data Source Requests"
          description="Track the status of your connection requests"
          icon={Database}
        />
        <Button
          onClick={() => fetchRequests(true)}
          variant="outline"
          disabled={refreshing}
        >
          <RefreshCw
            className={`h-4 w-4 mr-2 ${refreshing ? "animate-spin" : ""}`}
          />
          {refreshing ? "Refreshing..." : "Refresh"}
        </Button>
      </div>

      {requests.length === 0 ? (
        <Card className="glass-card border-border/50">
          <CardContent className="p-6 sm:p-12 text-center">
            <Database className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
            <h3 className="text-lg font-semibold mb-2">No Requests Yet</h3>
            <p className="text-sm sm:text-base text-muted-foreground mb-4">
              You haven't submitted any data source connection requests.
            </p>
            <Button
              onClick={() => (window.location.href = "/admin/data-sources")}
            >
              Submit New Request
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Card className="glass-card border-border/50">
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Ministry/Institution</TableHead>
                    <TableHead>Classification</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Requested</TableHead>
                    <TableHead>Synced Docs</TableHead>
                    <TableHead>Details</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {requests.map((request, index) => (
                    <motion.tr
                      key={request.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="border-border/40"
                    >
                      <TableCell className="font-medium">
                        {request.name}
                      </TableCell>
                      <TableCell>{request.ministry_name}</TableCell>
                      <TableCell>
                        {getClassificationBadge(request.data_classification)}
                      </TableCell>
                      <TableCell>
                        {getStatusBadge(request.request_status)}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {formatDateTime(request.requested_at)}
                      </TableCell>
                      <TableCell>
                        {request.request_status === "approved" ? (
                          <span className="text-sm">
                            {request.total_documents_synced || 0} docs
                          </span>
                        ) : (
                          <span className="text-sm text-muted-foreground">
                            -
                          </span>
                        )}
                      </TableCell>
                      <TableCell>
                        {request.request_status === "rejected" &&
                          request.rejection_reason && (
                            <Alert variant="destructive" className="mt-2">
                              <AlertDescription>
                                <strong>Rejected:</strong>{" "}
                                {request.rejection_reason}
                                {request.approved_by && (
                                  <div className="text-xs mt-1">
                                    By: {request.approved_by.name}
                                  </div>
                                )}
                              </AlertDescription>
                            </Alert>
                          )}
                        {(request.request_status === "approved" ||
                          request.request_status === "active") &&
                          request.approved_at && (
                            <div className="text-xs text-muted-foreground">
                              <div>
                                Approved {formatDateTime(request.approved_at)}
                              </div>
                              {request.approved_by && (
                                <div>By: {request.approved_by.name}</div>
                              )}
                              {request.last_sync_at && (
                                <div className="mt-1">
                                  Last sync:{" "}
                                  {formatDateTime(request.last_sync_at)}
                                </div>
                              )}
                            </div>
                          )}
                        {request.request_notes && (
                          <p className="text-xs text-muted-foreground mt-1">
                            Note: {request.request_notes}
                          </p>
                        )}
                      </TableCell>
                    </motion.tr>
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
