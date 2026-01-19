import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Progress } from "../ui/progress";
import { AlertTriangle, CheckCircle, XCircle, RefreshCw } from "lucide-react";
import { Button } from "../ui/button";

const QuotaStatus = ({ className = "" }) => {
  const [quotaData, setQuotaData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchQuotaStatus = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch("/api/quota/status");
      const data = await response.json();

      if (data.status === "success") {
        setQuotaData(data.quota_status);
        setLastUpdated(new Date());
      } else {
        setError(data.message || "Failed to fetch quota status");
      }
    } catch (err) {
      setError("Network error: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQuotaStatus();

    // Auto-refresh every 5 minutes
    const interval = setInterval(fetchQuotaStatus, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (percentage) => {
    if (percentage >= 90) return "text-red-600";
    if (percentage >= 70) return "text-yellow-600";
    return "text-green-600";
  };

  const getStatusIcon = (percentage) => {
    if (percentage >= 90) return <XCircle className="h-4 w-4 text-red-600" />;
    if (percentage >= 70)
      return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
    return <CheckCircle className="h-4 w-4 text-green-600" />;
  };

  const formatServiceName = (service) => {
    const names = {
      gemini_embeddings: "Embeddings",
      gemini_chat: "AI Chat",
      speech_to_text: "Voice Queries",
      vision_ocr: "OCR Processing",
    };
    return names[service] || service;
  };

  const formatPeriod = (period) => {
    const periods = {
      daily: "Today",
      monthly: "This Month",
      minute: "This Minute",
    };
    return periods[period] || period;
  };

  if (loading && !quotaData) {
    return (
      <Card className={className}>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <RefreshCw className="h-4 w-4 animate-spin" />
            Loading Quota Status...
          </CardTitle>
        </CardHeader>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <XCircle className="h-4 w-4 text-red-600" />
            Quota Status Error
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-red-600 mb-3">{error}</p>
          <Button
            onClick={fetchQuotaStatus}
            size="sm"
            variant="outline"
            disabled={loading}
          >
            <RefreshCw
              className={`h-3 w-3 mr-1 ${loading ? "animate-spin" : ""}`}
            />
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (!quotaData) {
    return null;
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium flex items-center justify-between">
          <span>API Quota Status</span>
          <Button
            onClick={fetchQuotaStatus}
            size="sm"
            variant="ghost"
            disabled={loading}
            className="h-6 w-6 p-0"
          >
            <RefreshCw className={`h-3 w-3 ${loading ? "animate-spin" : ""}`} />
          </Button>
        </CardTitle>
        {lastUpdated && (
          <p className="text-xs text-muted-foreground">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </p>
        )}
      </CardHeader>
      <CardContent className="space-y-4">
        {Object.entries(quotaData).map(([service, data]) => (
          <div key={service} className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">
                {formatServiceName(service)}
              </span>
              <Badge variant="outline" className="text-xs">
                Free Tier
              </Badge>
            </div>

            {/* Show quota for each period (daily, monthly, minute) */}
            {Object.entries(data).map(([period, stats]) => {
              if (
                period === "service" ||
                period === "limits" ||
                !stats ||
                typeof stats !== "object"
              ) {
                return null;
              }

              const percentage = stats.percentage || 0;
              const used = stats.used || 0;
              const limit = stats.limit || 0;
              const remaining = stats.remaining || 0;

              return (
                <div key={period} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">
                      {formatPeriod(period)}
                    </span>
                    <div className="flex items-center gap-1">
                      {getStatusIcon(percentage)}
                      <span className={getStatusColor(percentage)}>
                        {used}/{limit}
                      </span>
                    </div>
                  </div>
                  <Progress value={percentage} className="h-1.5" />
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>{percentage.toFixed(1)}% used</span>
                    <span>{remaining} remaining</span>
                  </div>
                </div>
              );
            })}
          </div>
        ))}

        {/* Warning message for high usage */}
        {Object.values(quotaData).some((service) =>
          Object.values(service).some(
            (period) =>
              period && typeof period === "object" && period.percentage >= 80,
          ),
        ) && (
          <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-yellow-600" />
              <p className="text-sm text-yellow-800">
                Some quotas are running low. Consider upgrading to paid tiers
                for higher limits.
              </p>
            </div>
          </div>
        )}

        {/* Info about free tier */}
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
          <p className="text-xs text-blue-800">
            <strong>Free Tier Limits:</strong> Embeddings (1,500/day), Chat
            (1,500/day), Voice (60 min/month), OCR (1,000/month)
          </p>
        </div>
      </CardContent>
    </Card>
  );
};

export default QuotaStatus;
