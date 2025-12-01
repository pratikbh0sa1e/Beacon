import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Bell,
  Check,
  Trash2,
  X,
  AlertCircle,
  FileText,
  Users,
  Shield,
} from "lucide-react";
import { notificationAPI } from "../../services/api";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { ScrollArea } from "../ui/scroll-area";
import { toast } from "sonner";
import { formatRelativeTime } from "../../utils/dateFormat";

const priorityConfig = {
  critical: {
    icon: AlertCircle,
    color: "text-red-500",
    bg: "bg-red-500/10",
    label: "🔥 Critical",
  },
  high: {
    icon: Shield,
    color: "text-orange-500",
    bg: "bg-orange-500/10",
    label: "⚠ High Priority",
  },
  medium: {
    icon: FileText,
    color: "text-blue-500",
    bg: "bg-blue-500/10",
    label: "📌 Medium",
  },
  low: {
    icon: Bell,
    color: "text-gray-500",
    bg: "bg-gray-500/10",
    label: "📨 Low",
  },
};

export const NotificationPanel = ({ onClose }) => {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    fetchNotifications();
  }, [filter]);

  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const params = {};
      if (filter === "unread") params.unread_only = true;
      if (filter !== "all" && filter !== "unread") params.priority = filter;

      const response = await notificationAPI.list(params);
      setNotifications(response.data.notifications || []);
    } catch (error) {
      console.error("Error fetching notifications:", error);
      // If endpoint doesn't exist yet, show placeholder
      setNotifications([
        {
          id: 1,
          title: "Notification System Ready",
          message:
            "The notification system is designed and ready for backend implementation.",
          type: "system",
          priority: "medium",
          read: false,
          created_at: new Date().toISOString(),
          action_label: "View Guide",
          action_url: "/admin/system",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleMarkRead = async (id) => {
    try {
      await notificationAPI.markRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, read: true } : n))
      );
      toast.success("Marked as read");
    } catch (error) {
      console.error("Error marking notification as read:", error);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationAPI.markAllRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
      toast.success("All notifications marked as read");
    } catch (error) {
      console.error("Error marking all as read:", error);
    }
  };

  const handleDelete = async (id) => {
    try {
      await notificationAPI.delete(id);
      setNotifications((prev) => prev.filter((n) => n.id !== id));
      toast.success("Notification deleted");
    } catch (error) {
      console.error("Error deleting notification:", error);
    }
  };

  const handleAction = (notification) => {
    if (notification.action_url) {
      window.location.href = notification.action_url;
      onClose();
    }
  };

  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <div className="w-96 max-w-[calc(100vw-2rem)]">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div className="flex items-center gap-2">
          <Bell className="h-5 w-5" />
          <h3 className="font-semibold">Notifications</h3>
          {unreadCount > 0 && (
            <Badge variant="destructive" className="h-5 px-2">
              {unreadCount}
            </Badge>
          )}
        </div>
        {unreadCount > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleMarkAllRead}
            className="text-xs"
          >
            Mark all read
          </Button>
        )}
      </div>

      {/* Filters */}
      <div className="flex gap-2 p-3 border-b border-border overflow-x-auto">
        {["all", "unread", "critical", "high", "medium", "low"].map((f) => (
          <Button
            key={f}
            variant={filter === f ? "default" : "outline"}
            size="sm"
            onClick={() => setFilter(f)}
            className="text-xs whitespace-nowrap"
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </Button>
        ))}
      </div>

      {/* Notifications List */}
      <ScrollArea className="h-[400px]">
        {loading ? (
          <div className="flex items-center justify-center h-40">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : notifications.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-40 text-muted-foreground">
            <Bell className="h-12 w-12 mb-2 opacity-50" />
            <p className="text-sm">No notifications</p>
          </div>
        ) : (
          <div className="p-2 space-y-2">
            <AnimatePresence>
              {notifications.map((notification) => {
                const config =
                  priorityConfig[notification.priority] ||
                  priorityConfig.medium;
                const Icon = config.icon;

                return (
                  <motion.div
                    key={notification.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, x: -100 }}
                    className={`p-3 rounded-lg border transition-colors ${
                      notification.read
                        ? "bg-secondary/30 border-border/50"
                        : "bg-card border-primary/30"
                    }`}
                  >
                    <div className="flex gap-3">
                      <div className={`${config.bg} p-2 rounded-lg h-fit`}>
                        <Icon className={`h-4 w-4 ${config.color}`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2 mb-1">
                          <h4 className="text-sm font-semibold truncate">
                            {notification.title}
                          </h4>
                          <span className="text-xs text-muted-foreground whitespace-nowrap">
                            {formatRelativeTime(notification.created_at)}
                          </span>
                        </div>
                        <p className="text-xs text-muted-foreground mb-2 line-clamp-2">
                          {notification.message}
                        </p>
                        <div className="flex items-center gap-2">
                          {notification.action_label && (
                            <Button
                              size="sm"
                              variant="outline"
                              className="h-7 text-xs"
                              onClick={() => handleAction(notification)}
                            >
                              {notification.action_label}
                            </Button>
                          )}
                          {!notification.read && (
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-7 text-xs"
                              onClick={() => handleMarkRead(notification.id)}
                            >
                              <Check className="h-3 w-3 mr-1" />
                              Mark read
                            </Button>
                          )}
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-7 text-xs ml-auto"
                            onClick={() => handleDelete(notification.id)}
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>
        )}
      </ScrollArea>

      {/* Footer */}
      {notifications.length > 0 && (
        <div className="p-3 border-t border-border text-center">
          <p className="text-xs text-muted-foreground">
            {notifications.length} notification
            {notifications.length !== 1 ? "s" : ""}
          </p>
        </div>
      )}
    </div>
  );
};
