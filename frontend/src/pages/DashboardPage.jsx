import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { FileText, Users, Upload, TrendingUp, Clock, CheckCircle, XCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { documentAPI, userAPI } from '../services/api';
import { PageHeader } from '../components/common/PageHeader';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { formatRelativeTime } from '../utils/dateFormat';
import { ADMIN_ROLES } from '../constants/roles';

const StatCard = ({ title, value, icon: Icon, trend, color = 'primary' }) => (
  <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} whileHover={{ y: -4 }}>
    <Card className="glass-card border-border/50 hover:border-primary/50 transition-colors">
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            <h3 className="text-3xl font-bold mt-2">{value}</h3>
            {trend && (
              <p className="text-xs text-muted-foreground mt-2 flex items-center gap-1">
                <TrendingUp className="h-3 w-3" />
                {trend}
              </p>
            )}
          </div>
          <div className={`h-12 w-12 rounded-xl bg-${color}/10 flex items-center justify-center`}>
            <Icon className={`h-6 w-6 text-${color}`} />
          </div>
        </div>
      </CardContent>
    </Card>
  </motion.div>
);

export const DashboardPage = () => {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const [stats, setStats] = useState({ documents: 0, users: 0, pending: 0 });
  const [recentDocs, setRecentDocs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const docsResponse = await documentAPI.listDocuments({ limit: 5 });
      setRecentDocs(docsResponse.data?.documents || []);
      setStats((prev) => ({ ...prev, documents: docsResponse.data?.total || 0 }));

      if (ADMIN_ROLES.includes(user?.role)) {
        const usersResponse = await userAPI.listUsers();
        setStats((prev) => ({
          ...prev,
          users: usersResponse.data?.length || 0,
          pending: usersResponse.data?.filter(u => !u.approved).length || 0,
        }));
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <PageHeader
        title={`Welcome back, ${user?.email?.split('@')[0] || 'User'}!`}
        description="Here's what's happening with your document system today."
      />

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <StatCard title="Total Documents" value={stats.documents} icon={FileText} trend="+12% from last month" />
        {ADMIN_ROLES.includes(user?.role) && (
          <>
            <StatCard title="Total Users" value={stats.users} icon={Users} trend="+5 new this week" color="accent" />
            <StatCard title="Pending Approvals" value={stats.pending} icon={Clock} color="warning" />
          </>
        )}
        <StatCard title="Documents Uploaded" value="24" icon={Upload} trend="This month" color="success" />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="glass-card border-border/50">
          <CardHeader>
            <CardTitle>Recent Documents</CardTitle>
            <CardDescription>Your recently accessed documents</CardDescription>
          </CardHeader>
          <CardContent>
            {recentDocs.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No documents yet</p>
              </div>
            ) : (
              <div className="space-y-3">
                {recentDocs.slice(0, 5).map((doc) => (
                  <motion.div
                    key={doc.id}
                    whileHover={{ x: 4 }}
                    className="flex items-center justify-between p-3 rounded-lg bg-secondary/50 hover:bg-secondary cursor-pointer"
                    onClick={() => navigate(`/documents/${doc.id}`)}
                  >
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <FileText className="h-5 w-5 text-primary flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="font-medium truncate">{doc.title}</p>
                        <p className="text-xs text-muted-foreground">{formatRelativeTime(doc.created_at)}</p>
                      </div>
                    </div>
                    <Badge variant="outline">{doc.category}</Badge>
                  </motion.div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="glass-card border-border/50">
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Common tasks and shortcuts</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button className="w-full justify-start neon-glow" onClick={() => navigate('/upload')}>
              <Upload className="h-4 w-4 mr-2" />
              Upload New Document
            </Button>
            <Button variant="outline" className="w-full justify-start" onClick={() => navigate('/documents')}>
              <FileText className="h-4 w-4 mr-2" />
              Browse Documents
            </Button>
            <Button variant="outline" className="w-full justify-start" onClick={() => navigate('/ai-chat')}>
              <TrendingUp className="h-4 w-4 mr-2" />
              Ask AI Assistant
            </Button>
          </CardContent>
        </Card>
      </div>

      {ADMIN_ROLES.includes(user?.role) && (
        <Card className="glass-card border-border/50">
          <CardHeader>
            <CardTitle>System Status</CardTitle>
            <CardDescription>Current system health and metrics</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="flex items-center gap-3 p-4 rounded-lg bg-success/10 border border-success/20">
                <CheckCircle className="h-8 w-8 text-success" />
                <div>
                  <p className="font-semibold">API Status</p>
                  <p className="text-sm text-muted-foreground">All systems operational</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-4 rounded-lg bg-primary/10 border border-primary/20">
                <TrendingUp className="h-8 w-8 text-primary" />
                <div>
                  <p className="font-semibold">Uptime</p>
                  <p className="text-sm text-muted-foreground">99.9% this month</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-4 rounded-lg bg-accent/10 border border-accent/20">
                <FileText className="h-8 w-8 text-accent" />
                <div>
                  <p className="font-semibold">Storage</p>
                  <p className="text-sm text-muted-foreground">45GB / 100GB used</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
