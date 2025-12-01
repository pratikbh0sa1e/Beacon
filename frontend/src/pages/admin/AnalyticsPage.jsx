import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  BarChart3,
  Users,
  FileText,
  Activity,
  TrendingUp,
  Clock,
  Download,
  Eye,
  Upload,
  CheckCircle,
  XCircle,
  Calendar,
} from "lucide-react";
import { auditAPI, documentAPI, userAPI } from "../../services/api";
import { PageHeader } from "../../components/common/PageHeader";
import { LoadingSpinner } from "../../components/common/LoadingSpinner";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import { toast } from "sonner";
import { formatRelativeTime } from "../../utils/dateFormat";

export const AnalyticsPage = () => {
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState("7");
  const [summary, setSummary] = useState(null);
  const [recentActivity, setRecentActivity] = useState([]);
  const [stats, setStats] = useState({
    totalUsers: 0,
    totalDocuments: 0,
    pendingApprovals: 0,
    activeUsers: 0,
  });

  useEffect(() => {
    fetchAnalytics();
  }, [timeRange]);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      // Fetch audit summary
      const summaryResponse = await auditAPI.getSummary(parseInt(timeRange));
      setSummary(summaryResponse.data);

      // Fetch recent activity
      const logsResponse = await auditAPI.getLogs({
        days: parseInt(timeRange),
        limit: 10,
      });
      setRecentActivity(logsResponse.data.logs || []);

      // Fetch additional stats
      const usersResponse = await userAPI.listUsers({ limit: 1000 });
      const docsResponse = await documentAPI.listDocuments({ limit: 1000 });

      setStats({
        totalUsers: usersResponse.data.total || 0,
        totalDocuments: docsResponse.data.total || 0,
        pendingApprovals:
          docsResponse.data.documents?.filter(
            (d) => d.approval_status === "pending"
          ).length || 0,
        activeUsers: summaryResponse.data.unique_users || 0,
      });
    } catch (error) {
      console.error("Error fetching analytics:", error);
      toast.error("Failed to load analytics data");
    } finally {
      setLoading(false);
    }
  };

  const getActionIcon = (action) => {
    switch (action) {
      case "login":
        return <Activity className="h-4 w-4 text-green-500" />;
      case "logout":
        return <Activity className="h-4 w-4 text-gray-500" />;
      case "upload_document":
        return <Upload className="h-4 w-4 text-blue-500" />;
      case "document_approved":
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case "document_rejected":
        return <XCircle className="h-4 w-4 text-red-500" />;
      case "user_approved":
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case "user_rejected":
        return <XCircle className="h-4 w-4 text-red-500" />;
      case "role_changed":
        return <Users className="h-4 w-4 text-purple-500" />;
      case "document_downloaded":
        return <Download className="h-4 w-4 text-blue-500" />;
      case "search_query":
        return <Eye className="h-4 w-4 text-yellow-500" />;
      default:
        return <Activity className="h-4 w-4 text-gray-500" />;
    }
  };

  const getActionLabel = (action) => {
    return action
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  if (loading) {
    return <LoadingSpinner text="Loading analytics..." />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Analytics Dashboard"
        description="System usage statistics and activity insights"
        icon={BarChart3}
        action={
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-48">
              <Calendar className="h-4 w-4 mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1">Last 24 Hours</SelectItem>
              <SelectItem value="7">Last 7 Days</SelectItem>
              <SelectItem value="30">Last 30 Days</SelectItem>
              <SelectItem value="90">Last 90 Days</SelectItem>
            </SelectContent>
          </Select>
        }
      />

      {/* Overview Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="glass-card border-border/50">
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-full bg-blue-500/10 flex items-center justify-center">
                  <Users className="h-6 w-6 text-blue-500" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats.totalUsers}</p>
                  <p className="text-sm text-muted-foreground">Total Users</p>
                </div>
              </div>
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
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-full bg-green-500/10 flex items-center justify-center">
                  <FileText className="h-6 w-6 text-green-500" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats.totalDocuments}</p>
                  <p className="text-sm text-muted-foreground">
                    Total Documents
                  </p>
                </div>
              </div>
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
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-full bg-yellow-500/10 flex items-center justify-center">
                  <Clock className="h-6 w-6 text-yellow-500" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats.pendingApprovals}</p>
                  <p className="text-sm text-muted-foreground">
                    Pending Approvals
                  </p>
                </div>
              </div>
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
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-full bg-purple-500/10 flex items-center justify-center">
                  <TrendingUp className="h-6 w-6 text-purple-500" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats.activeUsers}</p>
                  <p className="text-sm text-muted-foreground">Active Users</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Activity Summary */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Action Breakdown */}
        <Card className="glass-card border-border/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Activity Breakdown
            </CardTitle>
          </CardHeader>
          <CardContent>
            {summary?.action_breakdown ? (
              <div className="space-y-3">
                {Object.entries(summary.action_breakdown)
                  .sort(([, a], [, b]) => b - a)
                  .map(([action, count]) => (
                    <div
                      key={action}
                      className="flex items-center justify-between p-3 rounded-lg bg-secondary/50"
                    >
                      <div className="flex items-center gap-3">
                        {getActionIcon(action)}
                        <span className="text-sm font-medium">
                          {getActionLabel(action)}
                        </span>
                      </div>
                      <Badge variant="outline">{count}</Badge>
                    </div>
                  ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground text-center py-8">
                No activity data available
              </p>
            )}
          </CardContent>
        </Card>

        {/* Most Active Users */}
        <Card className="glass-card border-border/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Most Active Users
            </CardTitle>
          </CardHeader>
          <CardContent>
            {summary?.most_active_users?.length > 0 ? (
              <div className="space-y-3">
                {summary.most_active_users.map((user, index) => (
                  <div
                    key={user.user_id}
                    className="flex items-center justify-between p-3 rounded-lg bg-secondary/50"
                  >
                    <div className="flex items-center gap-3">
                      <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center text-sm font-bold">
                        {index + 1}
                      </div>
                      <div>
                        <p className="text-sm font-medium">{user.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {user.email}
                        </p>
                      </div>
                    </div>
                    <Badge variant="outline">{user.action_count} actions</Badge>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground text-center py-8">
                No user activity data available
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card className="glass-card border-border/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Recent Activity
          </CardTitle>
        </CardHeader>
        <CardContent>
          {recentActivity.length > 0 ? (
            <div className="space-y-3">
              {recentActivity.map((log) => (
                <motion.div
                  key={log.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="flex items-start gap-3 p-3 rounded-lg bg-secondary/50 hover:bg-secondary/70 transition-colors"
                >
                  <div className="mt-1">{getActionIcon(log.action)}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium">
                        {log.user.name}
                      </span>
                      <Badge variant="outline" className="text-xs">
                        {log.user.role}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {getActionLabel(log.action)}
                    </p>
                  </div>
                  <span className="text-xs text-muted-foreground whitespace-nowrap">
                    {formatRelativeTime(log.timestamp)}
                  </span>
                </motion.div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground text-center py-8">
              No recent activity
            </p>
          )}
        </CardContent>
      </Card>

      {/* Summary Stats */}
      {summary && (
        <Card className="glass-card border-border/50">
          <CardHeader>
            <CardTitle>Period Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="p-4 rounded-lg bg-secondary/50">
                <p className="text-sm text-muted-foreground mb-1">
                  Total Actions
                </p>
                <p className="text-2xl font-bold">{summary.total_actions}</p>
              </div>
              <div className="p-4 rounded-lg bg-secondary/50">
                <p className="text-sm text-muted-foreground mb-1">
                  Unique Users
                </p>
                <p className="text-2xl font-bold">{summary.unique_users}</p>
              </div>
              <div className="p-4 rounded-lg bg-secondary/50">
                <p className="text-sm text-muted-foreground mb-1">
                  Time Period
                </p>
                <p className="text-2xl font-bold">{summary.period_days} days</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
