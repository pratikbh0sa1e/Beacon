import { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  Plus,
  Search,
  MessageSquare,
  Trash2,
  Edit2,
  Check,
  X,
} from "lucide-react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { ScrollArea } from "../ui/scroll-area";
import { useChatStore } from "../../stores/chatStore";
import { cn } from "../../lib/utils";

export const ChatSidebar = ({ className }) => {
  const {
    sessions,
    currentSessionId,
    searchQuery,
    loading,
    clearCurrentSession,
    loadSession,
    deleteSession,
    renameSession,
    searchSessions,
    fetchSessions,
  } = useChatStore();

  const [editingId, setEditingId] = useState(null);
  const [editTitle, setEditTitle] = useState("");
  const [localSearch, setLocalSearch] = useState("");
  const [hoveredId, setHoveredId] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [, forceUpdate] = useState(0);

  useEffect(() => {
    // Debounce search
    const timer = setTimeout(() => {
      if (localSearch !== searchQuery) {
        searchSessions(localSearch);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [localSearch]);

  // Update timestamps every minute
  useEffect(() => {
    const interval = setInterval(() => {
      forceUpdate((n) => n + 1);
    }, 60000); // Update every minute

    return () => clearInterval(interval);
  }, []);

  const handleNewChat = () => {
    // Just clear current session, don't create new one
    // Session will be created when user sends first message
    clearCurrentSession();
  };

  const handleSelectSession = async (sessionId) => {
    if (sessionId !== currentSessionId) {
      await loadSession(sessionId);
    }
  };

  const handleDeleteSession = async (e, sessionId) => {
    e.stopPropagation();
    e.preventDefault();
    setDeleteConfirm(sessionId);
  };

  const confirmDelete = async () => {
    if (deleteConfirm) {
      console.log("User confirmed deletion");
      await deleteSession(deleteConfirm);
      setDeleteConfirm(null);
    }
  };

  const cancelDelete = () => {
    setDeleteConfirm(null);
  };

  const handleStartEdit = (e, session) => {
    e.stopPropagation();
    e.preventDefault();
    setEditingId(session.id);
    setEditTitle(session.title);
  };

  const handleSaveEdit = async (e, sessionId) => {
    e.stopPropagation();
    if (editTitle.trim()) {
      await renameSession(sessionId, editTitle.trim());
    }
    setEditingId(null);
  };

  const handleCancelEdit = (e) => {
    e.stopPropagation();
    setEditingId(null);
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <>
      {/* Delete Confirmation Modal - Rendered via Portal */}
      {deleteConfirm &&
        createPortal(
          <AnimatePresence>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-[9999] flex items-center justify-center"
            >
              {/* Backdrop */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={cancelDelete}
                className="absolute inset-0 bg-black/60 backdrop-blur-sm"
              />

              {/* Modal */}
              <motion.div
                initial={{ opacity: 0, scale: 0.9, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.9, y: 20 }}
                transition={{ type: "spring", duration: 0.3 }}
                className="relative w-full max-w-md mx-4"
              >
                <div className="bg-background border border-border rounded-lg shadow-2xl p-6">
                  <div className="flex items-start gap-4">
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ delay: 0.1, type: "spring" }}
                      className="flex-shrink-0 w-10 h-10 rounded-full bg-destructive/10 flex items-center justify-center"
                    >
                      <Trash2 className="h-5 w-5 text-destructive" />
                    </motion.div>

                    <div className="flex-1">
                      <motion.h3
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.15 }}
                        className="text-lg font-semibold mb-2"
                      >
                        Delete Chat?
                      </motion.h3>
                      <motion.p
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.2 }}
                        className="text-sm text-muted-foreground mb-6"
                      >
                        This action cannot be undone. This will permanently
                        delete the chat and all its messages.
                      </motion.p>

                      <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.25 }}
                        className="flex gap-3 justify-end"
                      >
                        <Button
                          variant="outline"
                          onClick={cancelDelete}
                          className="min-w-[80px]"
                        >
                          Cancel
                        </Button>
                        <Button
                          variant="destructive"
                          onClick={confirmDelete}
                          className="min-w-[80px] group"
                        >
                          <Trash2 className="h-4 w-4 mr-2 group-hover:scale-110 transition-transform" />
                          Delete
                        </Button>
                      </motion.div>
                    </div>
                  </div>
                </div>
              </motion.div>
            </motion.div>
          </AnimatePresence>,
          document.body
        )}

      <div className={cn("flex flex-col h-full bg-background/50", className)}>
        {/* Header */}
        <motion.div
          className="p-4 border-b border-border/50"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <Button
            onClick={handleNewChat}
            className="w-full neon-glow group relative overflow-hidden"
            size="sm"
          >
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-primary/20 to-primary/5"
              initial={{ x: "-100%" }}
              whileHover={{ x: "100%" }}
              transition={{ duration: 0.5 }}
            />
            <Plus className="h-4 w-4 mr-2 relative z-10" />
            <span className="relative z-10">New Chat</span>
          </Button>
        </motion.div>

        {/* Search */}
        <motion.div
          className="p-4 border-b border-border/50"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
        >
          <div className="relative group">
            <motion.div
              animate={{
                scale: localSearch ? 1.1 : 1,
                color: localSearch
                  ? "hsl(var(--primary))"
                  : "hsl(var(--muted-foreground))",
              }}
              transition={{ duration: 0.2 }}
            >
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 transition-colors" />
            </motion.div>
            <Input
              placeholder="Search chats..."
              value={localSearch}
              onChange={(e) => setLocalSearch(e.target.value)}
              className="pl-9 transition-all focus:ring-2 focus:ring-primary/20"
            />
          </div>
        </motion.div>

        {/* Sessions List */}
        <ScrollArea className="flex-1 overflow-y-auto">
          <div className="p-2 space-y-1 pb-4">
            <AnimatePresence>
              {sessions
                .sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt))
                .map((session, index) => (
                  <motion.div
                    key={session.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20, transition: { duration: 0.2 } }}
                    transition={{ delay: index * 0.05 }}
                    whileHover={{ scale: 1.02, x: 4 }}
                    whileTap={{ scale: 0.98 }}
                    onHoverStart={() => setHoveredId(session.id)}
                    onHoverEnd={() => setHoveredId(null)}
                    className={cn(
                      "p-2 rounded-lg cursor-pointer transition-all duration-200",
                      "hover:bg-accent/50 hover:shadow-md",
                      "relative overflow-hidden",
                      currentSessionId === session.id
                        ? "bg-accent/70 border border-primary/20 shadow-lg"
                        : "border border-transparent"
                    )}
                  >
                    {/* Active indicator */}
                    {currentSessionId === session.id && (
                      <motion.div
                        layoutId="activeSession"
                        className="absolute left-0 top-0 bottom-0 w-1 bg-primary rounded-r"
                        initial={false}
                        transition={{
                          type: "spring",
                          stiffness: 300,
                          damping: 30,
                        }}
                      />
                    )}
                    {editingId === session.id ? (
                      // Edit mode
                      <div
                        className="flex items-center gap-2"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Input
                          value={editTitle}
                          onChange={(e) => setEditTitle(e.target.value)}
                          onKeyPress={(e) => {
                            if (e.key === "Enter")
                              handleSaveEdit(e, session.id);
                            if (e.key === "Escape") handleCancelEdit(e);
                          }}
                          className="h-7 text-sm"
                          autoFocus
                        />
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-7 w-7"
                          onClick={(e) => handleSaveEdit(e, session.id)}
                        >
                          <Check className="h-3 w-3" />
                        </Button>
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-7 w-7"
                          onClick={handleCancelEdit}
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      </div>
                    ) : (
                      // View mode
                      <div
                        onClick={() => handleSelectSession(session.id)}
                        className="relative w-full"
                      >
                        <div className="flex items-start gap-1.5 w-full pr-12">
                          <motion.div
                            animate={{
                              rotate: hoveredId === session.id ? 360 : 0,
                              scale: hoveredId === session.id ? 1.1 : 1,
                            }}
                            transition={{ duration: 0.3 }}
                            className="flex-shrink-0"
                          >
                            <MessageSquare
                              className={cn(
                                "h-3.5 w-3.5 mt-0.5 transition-colors",
                                currentSessionId === session.id
                                  ? "text-primary"
                                  : "text-muted-foreground"
                              )}
                            />
                          </motion.div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-1 mb-0.5">
                              <p
                                className={cn(
                                  "text-xs font-medium transition-colors truncate",
                                  currentSessionId === session.id &&
                                    "text-primary"
                                )}
                                title={session.title}
                              >
                                {session.title.length > 30
                                  ? session.title.substring(0, 30) + "..."
                                  : session.title}
                              </p>
                            </div>
                            {session.lastMessage && (
                              <p className="text-[10px] text-muted-foreground truncate mt-0.5 leading-tight">
                                {session.lastMessage.length > 35
                                  ? session.lastMessage.substring(0, 35) + "..."
                                  : session.lastMessage}
                              </p>
                            )}
                            <div className="flex items-center gap-1.5 mt-0.5">
                              <p className="text-[10px] text-muted-foreground whitespace-nowrap">
                                {formatDate(session.updatedAt)}
                              </p>
                              <span className="text-[10px] text-muted-foreground">
                                •
                              </span>
                              <motion.span
                                className={cn(
                                  "text-[10px] px-1 py-0.5 rounded-full transition-colors whitespace-nowrap",
                                  currentSessionId === session.id
                                    ? "bg-primary/20 text-primary"
                                    : "bg-muted text-muted-foreground"
                                )}
                                whileHover={{ scale: 1.05 }}
                              >
                                {session.messageCount} msgs
                              </motion.span>
                            </div>
                          </div>
                        </div>
                        
                        {/* Action buttons - absolutely positioned */}
                        <AnimatePresence>
                          {hoveredId === session.id && (
                            <motion.div
                              initial={{ opacity: 0, scale: 0.8 }}
                              animate={{ opacity: 1, scale: 1 }}
                              exit={{ opacity: 0, scale: 0.8 }}
                              transition={{ duration: 0.15 }}
                              className="absolute top-2 right-2 flex gap-0.5 z-10"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <motion.button
                                whileHover={{ scale: 1.1 }}
                                whileTap={{ scale: 0.9 }}
                                className="h-6 w-6 flex items-center justify-center rounded hover:bg-accent text-muted-foreground hover:text-foreground transition-colors bg-background/90 backdrop-blur-sm shadow-sm border border-border/50"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleStartEdit(e, session);
                                }}
                                title="Rename"
                              >
                                <Edit2 className="h-3 w-3" />
                              </motion.button>
                              <motion.button
                                whileHover={{ scale: 1.1 }}
                                whileTap={{ scale: 0.9 }}
                                className="h-6 w-6 flex items-center justify-center rounded hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-colors bg-background/90 backdrop-blur-sm shadow-sm border border-border/50"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleDeleteSession(e, session.id);
                                }}
                                title="Delete"
                              >
                                <Trash2 className="h-3 w-3" />
                              </motion.button>
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>
                    )}
                  </motion.div>
                ))}
            </AnimatePresence>

            {sessions.length === 0 && !loading && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="text-center py-8 text-muted-foreground"
              >
                <motion.div
                  animate={{
                    rotate: [0, 10, -10, 0],
                    scale: [1, 1.1, 1.1, 1],
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    repeatDelay: 3,
                  }}
                >
                  <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50" />
                </motion.div>
                <p className="text-sm font-medium">No chats yet</p>
                <p className="text-xs mt-1">Create a new chat to get started</p>
              </motion.div>
            )}

            {loading && sessions.length === 0 && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-center py-8 text-muted-foreground"
              >
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  className="inline-block"
                >
                  <MessageSquare className="h-6 w-6 mx-auto mb-2" />
                </motion.div>
                <p className="text-sm">Loading chats...</p>
              </motion.div>
            )}
          </div>
        </ScrollArea>
      </div>
    </>
  );
};
