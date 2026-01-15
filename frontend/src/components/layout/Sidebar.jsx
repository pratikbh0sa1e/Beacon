import React from "react";
import { Link, useLocation } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  Home,
  FileText,
  Upload,
  MessageSquare,
  Users,
  Building2,
  BarChart3,
  Shield,
  Settings,
  X,
  Star,
  CheckCircle,
  StickyNote,
  Database,
  HelpCircle,
  Globe,
  FileSearch,
} from "lucide-react";
import { useAuthStore } from "../../stores/authStore";
import { ADMIN_ROLES, DOCUMENT_MANAGER_ROLES } from "../../constants/roles";
import { Button } from "../ui/button";
import { cn } from "../../lib/utils";

const menuItems = [
  { icon: Home, label: "Dashboard", path: "/", roles: [] },
  { icon: FileText, label: "Documents", path: "/documents", roles: [] },
  { icon: Star, label: "Bookmarks", path: "/bookmarks", roles: [] },
  { icon: StickyNote, label: "My Notes", path: "/notes", roles: [] },
  {
    icon: Upload,
    label: "Upload",
    path: "/upload",
    roles: DOCUMENT_MANAGER_ROLES,
  },
  { icon: MessageSquare, label: "AI Assistant", path: "/ai-chat", roles: [] },
  {
    icon: CheckCircle,
    label: "Document Approvals",
    path: "/approvals",
    roles: ["developer", "ministry_admin", "university_admin"],
  },
  {
    icon: FileSearch,
    label: "OCR Review",
    path: "/ocr-review",
    roles: [
      "developer",
      "ministry_admin",
      "university_admin",
      "document_officer",
    ],
  },
  {
    icon: Users,
    label: "User Management",
    path: "/admin/users",
    roles: ADMIN_ROLES,
  },
  {
    icon: Building2,
    label: "Institutions",
    path: "/admin/institutions",
    roles: ADMIN_ROLES,
  },
  {
    icon: BarChart3,
    label: "Analytics",
    path: "/admin/analytics",
    roles: ADMIN_ROLES,
  },
  {
    icon: Globe,
    label: "Web Scraping",
    path: "/admin/web-scraping",
    roles: ADMIN_ROLES,
  },
  {
    icon: Globe,
    label: "Enhanced Web Scraping",
    path: "/admin/web-scraping-enhanced",
    roles: ADMIN_ROLES,
  },
  {
    icon: Settings,
    label: "System Health",
    path: "/admin/system",
    roles: ["developer"],
  },
  { icon: HelpCircle, label: "Get Support", path: "/support", roles: [] },
];

// Data Source menu items - role-based structure
const getDataSourceMenuItems = (userRole) => {
  if (!userRole) return [];

  // Students and Faculty (public_viewer) should NOT see data source menu
  if (userRole === "student" || userRole === "public_viewer") {
    return [];
  }

  // Ministry Admin and University Admin see: Submit Request, My Requests
  if (userRole === "ministry_admin" || userRole === "university_admin") {
    return [
      {
        icon: Database,
        label: "Submit Request",
        path: "/admin/data-sources",
        roles: ["ministry_admin", "university_admin"],
      },
      {
        icon: Database,
        label: "My Requests",
        path: "/admin/my-data-source-requests",
        roles: ["ministry_admin", "university_admin"],
      },
    ];
  }

  // Developer sees: Pending Approvals, Active Sources, All Requests, Web Scraping
  if (userRole === "developer") {
    return [
      {
        icon: Shield,
        label: "Pending Approvals",
        path: "/admin/data-source-approvals",
        roles: ["developer"],
      },
      {
        icon: Database,
        label: "Active Sources",
        path: "/admin/active-sources",
        roles: ["developer"],
      },
      {
        icon: Database,
        label: "All Requests",
        path: "/admin/my-data-source-requests",
        roles: ["developer"],
      },
    ];
  }

  return [];
};

export const Sidebar = ({ isOpen, onClose }) => {
  const location = useLocation();
  const { user } = useAuthStore();

  const filteredMenuItems = menuItems.filter(
    (item) => item.roles.length === 0 || item.roles.includes(user?.role)
  );

  // Add data source menu items based on role
  const dataSourceItems = getDataSourceMenuItems(user?.role);
  const allMenuItems = [...filteredMenuItems, ...dataSourceItems];

  return (
    <>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm lg:hidden"
            onClick={onClose}
          />
        )}
      </AnimatePresence>

      <motion.aside
        initial={false}
        animate={{
          x: isOpen ? 0 : -280,
        }}
        className={cn(
          "fixed top-16 left-0 z-40 h-[calc(100vh-4rem)] w-64 border-r border-border/40 glass-card shadow-xl"
          // 'lg:!translate-x-0 lg:static lg:h-auto'
        )}
      >
        <div className="flex h-full flex-col">
          <div className="flex items-center justify-between p-4 lg:hidden">
            <span className="text-lg font-semibold">Menu</span>
            <Button variant="ghost" size="icon" onClick={onClose}>
              <X className="h-5 w-5" />
            </Button>
          </div>

          <nav className="flex-1 space-y-1 p-4 overflow-y-auto scrollbar-hide">
            {allMenuItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;

              return (
                // <Link key={item.path} to={item.path} onClick={() => onClose()}>
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => window.innerWidth < 1024 && onClose()}
                >
                  <motion.div
                    whileHover={{ x: 4 }}
                    whileTap={{ scale: 0.98 }}
                    className={cn(
                      "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                      isActive
                        ? "bg-primary/10 text-primary border border-primary/20 neon-glow"
                        : "text-muted-foreground hover:bg-secondary hover:text-foreground"
                    )}
                  >
                    <Icon className="h-5 w-5" />
                    <span>{item.label}</span>
                  </motion.div>
                </Link>
              );
            })}
          </nav>

          <div className="border-t border-border/40 p-4">
            <div className="rounded-lg bg-gradient-to-br from-primary/10 to-accent/10 p-4 border border-primary/20">
              <h4 className="text-sm font-semibold mb-1">Need Help?</h4>
              <p className="text-xs text-muted-foreground mb-3">
                Contact support or check documentation
              </p>
              <Link
                to="/support"
                onClick={() => window.innerWidth < 1024 && onClose()}
              >
                <Button size="sm" variant="outline" className="w-full">
                  Get Support
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </motion.aside>
    </>
  );
};
