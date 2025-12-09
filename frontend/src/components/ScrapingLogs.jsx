import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  RefreshCw,
  ChevronDown,
  ChevronUp,
  CheckCircle,
  XCircle,
  Clock,
  Activity,
  FileText,
  AlertCircle,
} from 'lucide-react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Alert, AlertDescription } from './ui/alert';
import axios from 'axios';

const API_BASE_URL = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api`;

const ScrapingLogs = () => {
  const [logs, setLogs] = useState([]);
  const [summary, setSummary] = useState(null);
  const [expandedLog, setExpandedLog] = useState(null);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchLogs = async () => {
    try {
      const [logsResponse, summaryResponse] = await Promise.all([
        axios.get(`${API_BASE_URL}/scraping-logs/recent?limit=50`),
        axios.get(`${API_BASE_URL}/scraping-logs/stats/summary`)
      ]);
      
      setLogs(logsResponse.data);
      setSummary(summaryResponse.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching logs:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
    
    let interval = null;
    if (autoRefresh) {
      interval = setInterval(fetchLogs, 5000);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'running':
        return <Clock className="h-4 w-4 text-blue-500" />;
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return null;
    }
  };

  const getStatusVariant = (status) => {
    switch (status) {
      case 'running':
        return 'default';
      case 'success':
        return 'success';
      case 'error':
        return 'destructive';
      default:
        return 'secondary';
    }
  };

  const formatDuration = (seconds) => {
    if (!seconds) return 'N/A';
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${minutes}m ${secs}s`;
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const toggleExpand = (logId) => {
    setExpandedLog(expandedLog === logId ? null : logId);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Activity className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Scraping Logs</h2>
          <p className="text-muted-foreground">Real-time monitoring of scraping activities</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant={autoRefresh ? 'default' : 'outline'}
            onClick={() => setAutoRefresh(!autoRefresh)}
            size="sm"
          >
            {autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
          </Button>
          <Button
            variant="outline"
            onClick={fetchLogs}
            size="sm"
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Total Logs</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{summary.total_logs}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Running</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-500">{summary.running}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Successful</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-500">{summary.successful}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Failed</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-500">{summary.failed}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Documents</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {summary.total_documents_scraped.toLocaleString()}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Pages</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{summary.total_pages_scraped}</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Logs List */}
      <Card>
        <CardHeader>
          <CardTitle>Activity Log</CardTitle>
          <CardDescription>Recent scraping operations</CardDescription>
        </CardHeader>
        <CardContent>
          {logs.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <FileText className="mx-auto h-12 w-12 mb-4 opacity-50" />
              <p>No scraping logs found</p>
            </div>
          ) : (
            <div className="space-y-4">
              {logs.map((log) => (
                <motion.div
                  key={log.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="border rounded-lg p-4"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        {getStatusIcon(log.status)}
                        <Badge variant={getStatusVariant(log.status)}>
                          {log.status.toUpperCase()}
                        </Badge>
                        <span className="font-semibold">{log.source_name}</span>
                      </div>
                      <p className="text-sm text-muted-foreground truncate">
                        {log.source_url}
                      </p>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => toggleExpand(log.id)}
                    >
                      {expandedLog === log.id ? (
                        <ChevronUp className="h-4 w-4" />
                      ) : (
                        <ChevronDown className="h-4 w-4" />
                      )}
                    </Button>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <p className="text-muted-foreground">Documents</p>
                      <p className="font-medium">
                        {log.documents_found} / {log.max_documents}
                      </p>
                      {log.status === 'running' && (
                        <Progress
                          value={(log.documents_found / log.max_documents) * 100}
                          className="mt-1"
                        />
                      )}
                    </div>
                    <div>
                      <p className="text-muted-foreground">Pages</p>
                      <p className="font-medium">
                        {log.pages_scraped} / {log.max_pages}
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Started</p>
                      <p className="font-medium">{formatDate(log.started_at)}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Duration</p>
                      <p className="font-medium">{formatDuration(log.execution_time)}</p>
                    </div>
                  </div>

                  {/* Expanded Details */}
                  {expandedLog === log.id && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="mt-4 pt-4 border-t space-y-4"
                    >
                      {/* Errors */}
                      {log.errors && log.errors.length > 0 && (
                        <div>
                          <h4 className="font-semibold mb-2 text-red-500">Errors:</h4>
                          {log.errors.map((error, idx) => (
                            <Alert key={idx} variant="destructive" className="mb-2">
                              <AlertCircle className="h-4 w-4" />
                              <AlertDescription>{error.message}</AlertDescription>
                            </Alert>
                          ))}
                        </div>
                      )}

                      {/* Messages */}
                      <div>
                        <h4 className="font-semibold mb-2">Activity Log:</h4>
                        <div className="bg-muted rounded-lg p-3 max-h-64 overflow-y-auto">
                          {log.messages && log.messages.map((message, idx) => (
                            <p
                              key={idx}
                              className="text-sm font-mono mb-1"
                            >
                              {message}
                            </p>
                          ))}
                        </div>
                      </div>
                    </motion.div>
                  )}
                </motion.div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default ScrapingLogs;
