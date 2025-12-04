import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Shield,
  CheckCircle,
  XCircle,
  Clock,
  FileText,
  User,
  Calendar,
  Eye,
  AlertCircle,
  Search,
  Filter,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { approvalAPI } from "../../services/api";
import { PageHeader } from "../../components/common/PageHeader";
import { LoadingSpinner } from "../../components/common/LoadingSpinner";
import { EmptyState } from "../../components/common/EmptyState";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Card, CardContent } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../../components/ui/dialog";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../../components/ui/tabs";
import { Textarea } from "../../components/ui/textarea";
import { toast } from "sonner";
import { formatRelativeTime } from "../../utils/dateFormat";

export const DocumentApprovalsPage = () => {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState([]);
  const [filteredDocuments, setFilteredDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [visibilityFilter, setVisibilityFilter] = useState("all");
  const [activeTab, setActiveTab] = useState("pending");
  const [actionLoading, setActionLoading] = useState(false);

  // Dialog states
  const [approveDialog, setApproveDialog] = useState(false);
  const [rejectDialog, setRejectDialog] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [notes, setNotes] = useState("");

  useEffect(() => {
    fetchDocuments();
  }, [activeTab]);

  useEffect(() => {
    filterDocuments();
  }, [documents, searchTerm, visibilityFilter, activeTab]);

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      let response;
      if (activeTab === "pending") {
        response = await approvalAPI.getPendingDocuments();
        setDocuments(response.data.pending_documents || []);
      } else if (activeTab === "approved") {
        response = await approvalAPI.getApprovedDocuments();
        setDocuments(response.data.approved_documents || []);
      } else if (activeTab === "rejected") {
        response = await approvalAPI.getRejectedDocuments();
        setDocuments(response.data.rejected_documents || []);
      }
    } catch (error) {
      console.error("Error fetching documents:", error);
      toast.error("Failed to load documents");
    } finally {
      setLoading(false);
    }
  };

  const filterDocuments = () => {
    let filtered = [...documents];

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(
        (doc) =>
          doc.filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
          doc.uploader?.name
            ?.toLowerCase()
            .includes(searchTerm.toLowerCase()) ||
          doc.uploader?.email?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Apply visibility filter
    if (visibilityFilter !== "all") {
      filtered = filtered.filter(
        (doc) => doc.visibility_level === visibilityFilter
      );
    }

    setFilteredDocuments(filtered);
  };

  const handleApproveClick = (doc) => {
    setSelectedDocument(doc);
    setNotes("");
    setApproveDialog(true);
  };

  const handleRejectClick = (doc) => {
    setSelectedDocument(doc);
    setNotes("");
    setRejectDialog(true);
  };

  const handleApprove = async () => {
    if (!selectedDocument) return;

    setActionLoading(true);
    try {
      await approvalAPI.approveDocument(selectedDocument.id, notes);
      toast.success(`Document "${selectedDocument.filename}" approved`);
      setApproveDialog(false);
      setSelectedDocument(null);
      setNotes("");
      fetchPendingDocuments();
    } catch (error) {
      console.error("Error approving document:", error);
      toast.error(error.response?.data?.detail || "Failed to approve document");
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!selectedDocument) return;

    if (!notes.trim()) {
      toast.error("Please provide a reason for rejection");
      return;
    }

    setActionLoading(true);
    try {
      await approvalAPI.rejectDocument(selectedDocument.id, notes);
      toast.success(`Document "${selectedDocument.filename}" rejected`);
      setRejectDialog(false);
      setSelectedDocument(null);
      setNotes("");
      fetchPendingDocuments();
    } catch (error) {
      console.error("Error rejecting document:", error);
      toast.error(error.response?.data?.detail || "Failed to reject document");
    } finally {
      setActionLoading(false);
    }
  };

  const getVisibilityColor = (level) => {
    switch (level) {
      case "public":
        return "default";
      case "institution_only":
        return "secondary";
      case "restricted":
        return "outline";
      case "confidential":
        return "destructive";
      default:
        return "default";
    }
  };

  const getVisibilityLabel = (level) => {
    return level.replace("_", " ").toUpperCase();
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Document Approvals"
        description="Review and approve pending document submissions"
        icon={Shield}
      />

      {/* Stats Cards */}
      <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 md:grid-cols-3">
        <Card className="glass-card border-border/50">
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 rounded-full bg-yellow-500/10 flex items-center justify-center">
                <Clock className="h-6 w-6 text-yellow-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">{documents.length}</p>
                <p className="text-sm text-muted-foreground">
                  Pending Approval
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card border-border/50">
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 rounded-full bg-blue-500/10 flex items-center justify-center">
                <FileText className="h-6 w-6 text-blue-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">{filteredDocuments.length}</p>
                <p className="text-sm text-muted-foreground">
                  Filtered Results
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card border-border/50">
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                <Shield className="h-6 w-6 text-primary" />
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {
                    documents.filter((d) => d.visibility_level === "restricted")
                      .length
                  }
                </p>
                <p className="text-sm text-muted-foreground">High Priority</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs
        value={activeTab}
        onValueChange={setActiveTab}
        className="space-y-6"
      >
        <TabsList className="grid w-full grid-cols-3 max-w-md">
          <TabsTrigger value="pending" className="flex items-center gap-2">
            <Clock className="h-4 w-4" />
            Pending
          </TabsTrigger>
          <TabsTrigger value="approved" className="flex items-center gap-2">
            <CheckCircle className="h-4 w-4" />
            Approved
          </TabsTrigger>
          <TabsTrigger value="rejected" className="flex items-center gap-2">
            <XCircle className="h-4 w-4" />
            Rejected
          </TabsTrigger>
        </TabsList>

        {/* Filters */}
        <Card className="glass-card border-border/50">
          <CardContent className="p-6">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search by filename or uploader..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>
              <Select
                value={visibilityFilter}
                onValueChange={setVisibilityFilter}
              >
                <SelectTrigger className="w-full sm:w-48">
                  <Filter className="h-4 w-4 mr-2" />
                  <SelectValue placeholder="Visibility" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Levels</SelectItem>
                  <SelectItem value="public">Public</SelectItem>
                  <SelectItem value="institution_only">
                    Institution Only
                  </SelectItem>
                  <SelectItem value="restricted">Restricted</SelectItem>
                  <SelectItem value="confidential">Confidential</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Pending Tab Content */}
        <TabsContent value="pending" className="space-y-4">
          {loading ? (
            <LoadingSpinner text="Loading pending documents..." />
          ) : documents.length === 0 ? (
            <EmptyState
              title="No pending approvals"
              description="All documents have been reviewed. Great job!"
              icon={CheckCircle}
            />
          ) : filteredDocuments.length === 0 ? (
            <EmptyState
              title="No documents found"
              description="Try adjusting your search or filter criteria."
              action={() => {
                setSearchTerm("");
                setVisibilityFilter("all");
              }}
              actionLabel="Clear Filters"
            />
          ) : (
            <div className="space-y-4">
              {filteredDocuments.map((doc, index) => (
                <motion.div
                  key={doc.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Card className="glass-card border-border/50 hover:border-primary/50 transition-all duration-300">
                    <CardContent className="p-6">
                      <div className="flex flex-col lg:flex-row lg:items-center gap-4">
                        {/* Document Info */}
                        <div className="flex-1 space-y-3">
                          <div className="flex items-start gap-3">
                            <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                              <FileText className="h-5 w-5 text-primary" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <h3 className="font-semibold text-lg truncate">
                                {doc.filename}
                              </h3>
                              <div className="flex flex-wrap items-center gap-2 mt-1">
                                <Badge
                                  variant={getVisibilityColor(
                                    doc.visibility_level
                                  )}
                                >
                                  {getVisibilityLabel(doc.visibility_level)}
                                </Badge>
                                <Badge variant="outline">
                                  {doc.file_type?.toUpperCase() || "FILE"}
                                </Badge>
                              </div>
                            </div>
                          </div>

                          {/* Uploader Info */}
                          <div className="flex items-center gap-4 text-sm text-muted-foreground pl-13">
                            <div className="flex items-center gap-2">
                              <User className="h-4 w-4" />
                              <span>
                                {doc.uploader.name} ({doc.uploader.email})
                              </span>
                            </div>
                            <div className="flex items-center gap-2">
                              <Calendar className="h-4 w-4" />
                              <span>{formatRelativeTime(doc.uploaded_at)}</span>
                            </div>
                          </div>

                          {/* Warning for high-priority documents */}
                          {doc.visibility_level === "restricted" ||
                          doc.visibility_level === "confidential" ? (
                            <div className="flex items-center gap-2 text-sm text-yellow-600 dark:text-yellow-500 pl-13">
                              <AlertCircle className="h-4 w-4" />
                              <span>
                                High priority - requires careful review
                              </span>
                            </div>
                          ) : null}
                        </div>

                        {/* Actions */}
                        <div className="flex flex-col sm:flex-row gap-2 lg:flex-col">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => navigate(`/documents/${doc.id}`)}
                            className="w-full sm:w-auto"
                          >
                            <Eye className="h-4 w-4 mr-2" />
                            Review
                          </Button>
                          <Button
                            variant="default"
                            size="sm"
                            onClick={() => handleApproveClick(doc)}
                            className="w-full sm:w-auto bg-green-600 hover:bg-green-700"
                          >
                            <CheckCircle className="h-4 w-4 mr-2" />
                            Approve
                          </Button>
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => handleRejectClick(doc)}
                            className="w-full sm:w-auto"
                          >
                            <XCircle className="h-4 w-4 mr-2" />
                            Reject
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Approved Tab Content */}
        <TabsContent value="approved" className="space-y-4">
          {loading ? (
            <LoadingSpinner text="Loading approved documents..." />
          ) : documents.length === 0 ? (
            <EmptyState
              title="No approved documents"
              description="No documents have been approved yet."
              icon={CheckCircle}
            />
          ) : filteredDocuments.length === 0 ? (
            <EmptyState
              title="No documents found"
              description="Try adjusting your search or filter criteria."
              action={() => {
                setSearchTerm("");
                setVisibilityFilter("all");
              }}
              actionLabel="Clear Filters"
            />
          ) : (
            <div className="space-y-4">
              {filteredDocuments.map((doc, index) => (
                <motion.div
                  key={doc.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Card className="glass-card border-border/50 hover:border-green-500/50 transition-all duration-300">
                    <CardContent className="p-6">
                      <div className="flex flex-col lg:flex-row lg:items-center gap-4">
                        <div className="flex-1 space-y-3">
                          <div className="flex items-start gap-3">
                            <div className="h-10 w-10 rounded-lg bg-green-500/10 flex items-center justify-center flex-shrink-0">
                              <CheckCircle className="h-5 w-5 text-green-500" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <h3 className="font-semibold text-lg truncate">
                                {doc.filename}
                              </h3>
                              <div className="flex flex-wrap items-center gap-2 mt-1">
                                <Badge
                                  variant={getVisibilityColor(
                                    doc.visibility_level
                                  )}
                                >
                                  {getVisibilityLabel(doc.visibility_level)}
                                </Badge>
                                <Badge variant="outline">
                                  {doc.file_type?.toUpperCase() || "FILE"}
                                </Badge>
                                <Badge className="bg-green-500/10 text-green-500 border-green-500/20">
                                  Approved
                                </Badge>
                              </div>
                            </div>
                          </div>

                          <div className="flex items-center gap-4 text-sm text-muted-foreground pl-13">
                            <div className="flex items-center gap-2">
                              <User className="h-4 w-4" />
                              <span>Uploaded by {doc.uploader.name}</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <CheckCircle className="h-4 w-4" />
                              <span>
                                Approved by {doc.approver?.name || "Unknown"}
                              </span>
                            </div>
                            <div className="flex items-center gap-2">
                              <Calendar className="h-4 w-4" />
                              <span>{formatRelativeTime(doc.approved_at)}</span>
                            </div>
                          </div>
                        </div>

                        <div className="flex flex-col sm:flex-row gap-2 lg:flex-col">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => navigate(`/documents/${doc.id}`)}
                            className="w-full sm:w-auto"
                          >
                            <Eye className="h-4 w-4 mr-2" />
                            View
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Rejected Tab Content */}
        <TabsContent value="rejected" className="space-y-4">
          {loading ? (
            <LoadingSpinner text="Loading rejected documents..." />
          ) : documents.length === 0 ? (
            <EmptyState
              title="No rejected documents"
              description="No documents have been rejected yet."
              icon={XCircle}
            />
          ) : filteredDocuments.length === 0 ? (
            <EmptyState
              title="No documents found"
              description="Try adjusting your search or filter criteria."
              action={() => {
                setSearchTerm("");
                setVisibilityFilter("all");
              }}
              actionLabel="Clear Filters"
            />
          ) : (
            <div className="space-y-4">
              {filteredDocuments.map((doc, index) => (
                <motion.div
                  key={doc.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Card className="glass-card border-border/50 hover:border-red-500/50 transition-all duration-300">
                    <CardContent className="p-6">
                      <div className="flex flex-col lg:flex-row lg:items-center gap-4">
                        <div className="flex-1 space-y-3">
                          <div className="flex items-start gap-3">
                            <div className="h-10 w-10 rounded-lg bg-red-500/10 flex items-center justify-center flex-shrink-0">
                              <XCircle className="h-5 w-5 text-red-500" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <h3 className="font-semibold text-lg truncate">
                                {doc.filename}
                              </h3>
                              <div className="flex flex-wrap items-center gap-2 mt-1">
                                <Badge
                                  variant={getVisibilityColor(
                                    doc.visibility_level
                                  )}
                                >
                                  {getVisibilityLabel(doc.visibility_level)}
                                </Badge>
                                <Badge variant="outline">
                                  {doc.file_type?.toUpperCase() || "FILE"}
                                </Badge>
                                <Badge className="bg-red-500/10 text-red-500 border-red-500/20">
                                  Rejected
                                </Badge>
                              </div>
                            </div>
                          </div>

                          <div className="flex items-center gap-4 text-sm text-muted-foreground pl-13">
                            <div className="flex items-center gap-2">
                              <User className="h-4 w-4" />
                              <span>Uploaded by {doc.uploader.name}</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <XCircle className="h-4 w-4" />
                              <span>
                                Rejected by {doc.rejector?.name || "Unknown"}
                              </span>
                            </div>
                            <div className="flex items-center gap-2">
                              <Calendar className="h-4 w-4" />
                              <span>{formatRelativeTime(doc.rejected_at)}</span>
                            </div>
                          </div>
                        </div>

                        <div className="flex flex-col sm:flex-row gap-2 lg:flex-col">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => navigate(`/documents/${doc.id}`)}
                            className="w-full sm:w-auto"
                          >
                            <Eye className="h-4 w-4 mr-2" />
                            View
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Approve Dialog */}
      <Dialog open={approveDialog} onOpenChange={setApproveDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Approve Document</DialogTitle>
            <DialogDescription>
              Are you sure you want to approve "{selectedDocument?.filename}"?
              This will make it accessible according to its visibility level.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Notes (Optional)</label>
              <Textarea
                placeholder="Add any notes about this approval..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setApproveDialog(false)}
              disabled={actionLoading}
            >
              Cancel
            </Button>
            <Button
              onClick={handleApprove}
              disabled={actionLoading}
              className="bg-green-600 hover:bg-green-700"
            >
              {actionLoading ? (
                <>
                  <Clock className="h-4 w-4 mr-2 animate-spin" />
                  Approving...
                </>
              ) : (
                <>
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Approve
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Reject Dialog */}
      <Dialog open={rejectDialog} onOpenChange={setRejectDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reject Document</DialogTitle>
            <DialogDescription>
              Are you sure you want to reject "{selectedDocument?.filename}"?
              This action will prevent the document from being accessible.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">
                Reason for Rejection <span className="text-destructive">*</span>
              </label>
              <Textarea
                placeholder="Please provide a reason for rejecting this document..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={4}
                className="resize-none"
              />
              <p className="text-xs text-muted-foreground">
                This reason will be logged and may be shared with the uploader.
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setRejectDialog(false)}
              disabled={actionLoading}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleReject}
              disabled={actionLoading || !notes.trim()}
            >
              {actionLoading ? (
                <>
                  <Clock className="h-4 w-4 mr-2 animate-spin" />
                  Rejecting...
                </>
              ) : (
                <>
                  <XCircle className="h-4 w-4 mr-2" />
                  Reject
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};
