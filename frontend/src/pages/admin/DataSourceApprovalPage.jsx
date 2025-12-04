import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Database,
  Check,
  X,
  TestTube,
  User,
  Building2,
  CheckCircle,
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
import { Textarea } from "../../components/ui/textarea";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "../../components/ui/alert-dialog";
import { formatDateTime } from "../../utils/dateFormat";
import { toast } from "sonner";
import { formatErrorForToast } from "../../utils/errorHandlers";

export const DataSourceApprovalPage = () => {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionDialog, setActionDialog] = useState({
    open: false,
    request: null,
    action: null,
  });
  const [rejectionReason, setRejectionReason] = useState("");
  const [processingAction, setProcessingAction] = useState(false);

  useEffect(() => {
    fetchPendingRequests();
  }, []);

  const fetchPendingRequests = async () => {
    setLoading(true);
    try {
      const response = await dataSourceAPI.pendingRequests();
      setRequests(response.data.requests || []);
    } catch (error) {
      console.error("Error fetching requests:", error);
      toast.error(
        formatErrorForToast(error, "Failed to load pending requests")
      );
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (requestId) => {
    setProcessingAction(true);
    try {
      await dataSourceAPI.approve(requestId);
      toast.success("✅ Request approved! Sync started in background.");
      fetchPendingRequests();
    } catch (error) {
      console.error("Approve error:", error);
      toast.error(formatErrorForToast(error, "Failed to approve request"));
    } finally {
      setProcessingAction(false);
      setActionDialog({ open: false, request: null, action: null });
    }
  };

  const handleReject = async (requestId) => {
    if (!rejectionReason.trim()) {
      toast.error("⚠️ Rejection reason is required and cannot be empty");
      return;
    }

    if (rejectionReason.trim().length < 10) {
      toast.error("⚠️ Rejection reason must be at least 10 characters");
      return;
    }

    setProcessingAction(true);
    try {
      await dataSourceAPI.reject(requestId, rejectionReason);
      toast.success("✅ Request rejected. Requester has been notified.");
      fetchPendingRequests();
      setRejectionReason("");
    } catch (error) {
      console.error("Reject error:", error);
      toast.error(formatErrorForToast(error, "Failed to reject request"));
    } finally {
      setProcessingAction(false);
      setActionDialog({ open: false, request: null, action: null });
    }
  };

  const getClassificationBadge = (classification) => {
    const colors = {
      public: "bg-blue-500/10 text-blue-500 border-blue-500/20",
      educational: "bg-purple-500/10 text-purple-500 border-purple-500/20",
      confidential: "bg-red-500/10 text-red-500 border-red-500/20",
      institutional: "bg-green-500/10 text-green-500 border-green-500/20",
    };

    return (
      <Badge className={colors[classification] || ""}>
        {classification?.charAt(0).toUpperCase() + classification?.slice(1)}
      </Badge>
    );
  };

  if (loading) {
    return <LoadingSpinner text="Loading pending requests..." />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Data Source Approvals"
        description="Review and approve connection requests"
        icon={Database}
      />

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="glass-card border-border/50">
          <CardContent className="p-6">
            <p className="text-sm text-muted-foreground">Pending Requests</p>
            <p className="text-3xl font-bold mt-2 text-warning">
              {requests.length}
            </p>
          </CardContent>
        </Card>
      </div>

      {requests.length === 0 ? (
        <Card className="glass-card border-border/50">
          <CardContent className="p-6 sm:p-12 text-center">
            <CheckCircle className="h-12 w-12 mx-auto mb-4 text-success" />
            <h3 className="text-lg font-semibold mb-2">All Caught Up!</h3>
            <p className="text-sm sm:text-base text-muted-foreground">
              No pending data source requests at the moment.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {requests.map((request, index) => (
            <motion.div
              key={request.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card className="glass-card border-border/50">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-xl">{request.name}</CardTitle>
                      <p className="text-sm text-muted-foreground mt-1">
                        {request.ministry_name}
                      </p>
                    </div>
                    {getClassificationBadge(request.data_classification)}
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {request.description && (
                    <p className="text-sm text-muted-foreground">
                      {request.description}
                    </p>
                  )}

                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="space-y-2">
                      <h4 className="text-sm font-semibold">
                        Connection Details
                      </h4>
                      <div className="text-sm space-y-1">
                        <p className="break-all">
                          <span className="text-muted-foreground">Host:</span>{" "}
                          {request.host}:{request.port}
                        </p>
                        <p className="break-all">
                          <span className="text-muted-foreground">
                            Database:
                          </span>{" "}
                          {request.database_name}
                        </p>
                        <p className="break-all">
                          <span className="text-muted-foreground">
                            Username:
                          </span>{" "}
                          {request.username}
                        </p>
                        <p className="break-all">
                          <span className="text-muted-foreground">Table:</span>{" "}
                          {request.table_name}
                        </p>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <h4 className="text-sm font-semibold">Request Info</h4>
                      <div className="text-sm space-y-1">
                        <p className="flex items-center gap-2">
                          <User className="h-3 w-3 flex-shrink-0" />
                          <span className="break-all">
                            {request.requested_by?.name} (
                            {request.requested_by?.role})
                          </span>
                        </p>
                        {request.institution && (
                          <p className="flex items-center gap-2">
                            <Building2 className="h-3 w-3 flex-shrink-0" />
                            <span className="break-all">
                              {request.institution.name}
                            </span>
                          </p>
                        )}
                        <p className="break-all">
                          <span className="text-muted-foreground">
                            Requested:
                          </span>{" "}
                          {formatDateTime(request.requested_at)}
                        </p>
                      </div>
                    </div>
                  </div>

                  {request.request_notes && (
                    <div className="p-3 bg-secondary/50 rounded-lg">
                      <p className="text-sm">
                        <strong>Notes:</strong> {request.request_notes}
                      </p>
                    </div>
                  )}

                  <div className="flex flex-col sm:flex-row gap-2 pt-4">
                    <Button
                      onClick={() =>
                        setActionDialog({
                          open: true,
                          request,
                          action: "approve",
                        })
                      }
                      className="flex-1"
                    >
                      <Check className="h-4 w-4 mr-2" />
                      Approve
                    </Button>
                    <Button
                      onClick={() =>
                        setActionDialog({
                          open: true,
                          request,
                          action: "reject",
                        })
                      }
                      variant="destructive"
                      className="flex-1"
                    >
                      <X className="h-4 w-4 mr-2" />
                      Reject
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      )}

      <AlertDialog
        open={actionDialog.open}
        onOpenChange={(open) => {
          setActionDialog({ ...actionDialog, open });
          if (!open) setRejectionReason("");
        }}
      >
        <AlertDialogContent className="glass-card">
          <AlertDialogHeader>
            <AlertDialogTitle>
              {actionDialog.action === "approve"
                ? "Approve Data Source Request"
                : "Reject Data Source Request"}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {actionDialog.action === "approve" ? (
                <>
                  Are you sure you want to approve the connection to{" "}
                  <strong>{actionDialog.request?.name}</strong>?
                  <br />
                  <br />
                  This will:
                  <ul className="list-disc list-inside mt-2 space-y-1">
                    <li>Enable the data source</li>
                    <li>Start automatic sync</li>
                    <li>Make documents available based on classification</li>
                  </ul>
                </>
              ) : (
                <>
                  Are you sure you want to reject the connection to{" "}
                  <strong>{actionDialog.request?.name}</strong>?
                  <div className="mt-4">
                    <label className="text-sm font-medium">
                      Rejection Reason (Required):
                    </label>
                    <Textarea
                      value={rejectionReason}
                      onChange={(e) => setRejectionReason(e.target.value)}
                      placeholder="Explain why this request is being rejected..."
                      className="mt-2"
                      rows={3}
                    />
                  </div>
                </>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={processingAction}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (actionDialog.action === "approve") {
                  handleApprove(actionDialog.request?.id);
                } else {
                  handleReject(actionDialog.request?.id);
                }
              }}
              disabled={processingAction}
              className={
                actionDialog.action === "reject"
                  ? "bg-destructive hover:bg-destructive/90"
                  : ""
              }
            >
              {processingAction ? (
                <>
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{
                      duration: 1,
                      repeat: Infinity,
                      ease: "linear",
                    }}
                    className="mr-2"
                  >
                    <CheckCircle className="h-4 w-4" />
                  </motion.div>
                  Processing...
                </>
              ) : (
                "Confirm"
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};
