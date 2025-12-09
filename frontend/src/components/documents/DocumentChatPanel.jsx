import { useState, useEffect, useRef } from "react";
import { Send, Users, Loader2, Sparkles, User } from "lucide-react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Badge } from "../ui/badge";
import { ScrollArea } from "../ui/scroll-area";
import { Avatar, AvatarFallback } from "../ui/avatar";
import { toast } from "sonner";
import { useAuthStore } from "../../stores/authStore";
import { formatDateTime } from "../../utils/dateFormat";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const DocumentChatPanel = ({ documentId }) => {
  const { user, token } = useAuthStore();
  const [messages, setMessages] = useState([]);
  const [participants, setParticipants] = useState([]);
  const [newMessage, setNewMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [beaconThinking, setBeaconThinking] = useState(false);
  const [replyTo, setReplyTo] = useState(null);
  const [replyPrefix, setReplyPrefix] = useState("");
  const [userSuggestions, setUserSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  // Start with all threads collapsed by default
  const [collapsedThreads, setCollapsedThreads] = useState(() => {
    // Will be populated when messages load
    return new Set();
  });

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const eventSourceRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (documentId) {
      loadMessages();
      loadParticipants();
      connectSSE();
    }

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, [documentId]);

  const loadMessages = async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/documents/${documentId}/chat/messages?limit=50`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setMessages(data);

        // Collapse all threads by default
        const parentIds = new Set(
          data.filter((m) => !m.parent_message_id).map((m) => m.id)
        );
        setCollapsedThreads(parentIds);
      }
    } catch (error) {
      console.error("Error loading messages:", error);
      toast.error("Failed to load chat messages");
    } finally {
      setLoading(false);
    }
  };

  const loadParticipants = async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/documents/${documentId}/chat/participants`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setParticipants(data);
      }
    } catch (error) {
      console.error("Error loading participants:", error);
    }
  };

  const connectSSE = () => {
    const eventSource = new EventSource(
      `${API_BASE_URL}/documents/${documentId}/chat/stream?token=${token}`
    );

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === "message") {
          setMessages((prev) => [...prev, data.data]);
        } else if (data.type === "beacon_thinking") {
          setBeaconThinking(true);
        } else if (data.type === "beacon_error") {
          setBeaconThinking(false);
          toast.error(data.data.message);
        } else if (
          data.type === "participant_joined" ||
          data.type === "participant_left"
        ) {
          loadParticipants();
        }
      } catch (error) {
        console.error("Error parsing SSE message:", error);
      }
    };

    eventSource.onerror = () => {
      console.error("SSE connection error");
      eventSource.close();
      setTimeout(() => connectSSE(), 5000);
    };

    eventSourceRef.current = eventSource;
  };

  const searchUsers = async (query) => {
    if (!query || query.length < 2) {
      setUserSuggestions([]);
      return;
    }

    try {
      const response = await fetch(
        `${API_BASE_URL}/documents/${documentId}/chat/search-users?query=${encodeURIComponent(
          query
        )}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setUserSuggestions(data);
      }
    } catch (error) {
      console.error("Error searching users:", error);
    }
  };

  const handleInputChange = (e) => {
    let value = e.target.value;

    // If replying, ensure the @mention prefix cannot be removed
    if (replyPrefix) {
      if (!value.startsWith(replyPrefix)) {
        // If user tries to delete the prefix, restore it
        value = replyPrefix;
      }
    }

    setNewMessage(value);

    const lastAtIndex = value.lastIndexOf("@");
    if (lastAtIndex !== -1 && lastAtIndex === value.length - 1) {
      setShowSuggestions(true);
      searchUsers("");
    } else if (lastAtIndex !== -1) {
      const query = value.slice(lastAtIndex + 1);
      if (!query.includes(" ")) {
        setShowSuggestions(true);
        searchUsers(query);
      } else {
        setShowSuggestions(false);
      }
    } else {
      setShowSuggestions(false);
    }
  };

  const insertMention = (user) => {
    const lastAtIndex = newMessage.lastIndexOf("@");
    const beforeMention = newMessage.slice(0, lastAtIndex);
    setNewMessage(`${beforeMention}@${user.name} `);
    setShowSuggestions(false);
    inputRef.current?.focus();
  };

  const sendMessage = async () => {
    // Get the actual message content (excluding reply prefix)
    const actualMessage = replyPrefix
      ? newMessage.slice(replyPrefix.length).trim()
      : newMessage.trim();

    // Validate that there's actual content beyond the @mention
    if (!actualMessage || sending) {
      if (!actualMessage && replyPrefix) {
        toast.error("Please enter a message");
      }
      return;
    }

    setSending(true);
    setBeaconThinking(newMessage.toLowerCase().includes("@beacon"));

    try {
      const response = await fetch(
        `${API_BASE_URL}/documents/${documentId}/chat/messages`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            content: newMessage,
            parent_message_id: replyTo?.id || null,
          }),
        }
      );

      if (response.ok) {
        setNewMessage("");
        setReplyTo(null);
        setReplyPrefix("");
        setBeaconThinking(false);
      } else {
        const error = await response.json();
        toast.error(error.detail || "Failed to send message");
        setBeaconThinking(false);
      }
    } catch (error) {
      console.error("Error sending message:", error);
      toast.error("Failed to send message");
      setBeaconThinking(false);
    } finally {
      setSending(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const getInitials = (name) => {
    if (!name) return "?";
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  const renderMessage = (message, isReply = false) => {
    const isBeacon = message.message_type === "beacon";
    const isCurrentUser = message.user_id === user?.id;

    // Find replies to this message
    const replies = messages.filter((m) => m.parent_message_id === message.id);
    const isCollapsed = collapsedThreads.has(message.id);

    return (
      <div key={message.id} className={isReply ? "ml-8 mt-2" : ""}>
        <div
          className={`flex gap-3 ${
            isReply ? "border-l-2 border-primary/30 pl-4" : ""
          }`}
        >
          <Avatar className="h-8 w-8 flex-shrink-0">
            <AvatarFallback
              className={
                isBeacon
                  ? "bg-gradient-to-br from-primary to-accent text-primary-foreground"
                  : "bg-muted"
              }
            >
              {isBeacon ? (
                <Sparkles className="h-4 w-4" />
              ) : (
                getInitials(message.user_name)
              )}
            </AvatarFallback>
          </Avatar>

          <div className="flex-1 space-y-1">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-sm">
                {message.user_name || "Unknown"}
              </span>
              {isBeacon && (
                <Badge
                  variant="secondary"
                  className="text-xs bg-primary/10 text-primary"
                >
                  AI Assistant
                </Badge>
              )}
              <span className="text-xs text-muted-foreground">
                {formatDateTime(message.created_at)}
              </span>
            </div>

            <div
              className={`rounded-lg p-3 ${
                isBeacon
                  ? "bg-gradient-to-br from-primary/10 to-accent/10 border border-primary/20"
                  : isCurrentUser
                  ? "bg-primary/10 border border-primary/20"
                  : "bg-muted/50 border border-border/50"
              }`}
            >
              <p className="text-sm whitespace-pre-wrap break-words">
                {message.content}
              </p>

              {message.citations && message.citations.length > 0 && (
                <div className="mt-2 pt-2 border-t border-border/50">
                  <p className="text-xs text-muted-foreground mb-1">Sources:</p>
                  {message.citations.map((citation, idx) => (
                    <div key={idx} className="text-xs text-muted-foreground">
                      • {citation.source}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="flex items-center gap-2">
              {!isBeacon && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 text-xs"
                  onClick={() => {
                    setReplyTo(message);
                    const prefix = `@${message.user_name} `;
                    setReplyPrefix(prefix);
                    setNewMessage(prefix);
                    inputRef.current?.focus();
                  }}
                >
                  Reply
                </Button>
              )}

              {/* Collapse/Expand button for threads with replies */}
              {!isReply && replies.length > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 text-xs"
                  onClick={() => toggleThread(message.id)}
                >
                  {isCollapsed
                    ? `Show ${replies.length} ${
                        replies.length === 1 ? "reply" : "replies"
                      }`
                    : "Hide replies"}
                </Button>
              )}
            </div>
          </div>
        </div>

        {/* Render replies as threaded conversation */}
        {!isReply && replies.length > 0 && !isCollapsed && (
          <div className="mt-2 space-y-2">
            {replies.map((reply) => renderMessage(reply, true))}
          </div>
        )}
      </div>
    );
  };

  const toggleThread = (messageId) => {
    setCollapsedThreads((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(messageId)) {
        newSet.delete(messageId);
      } else {
        newSet.add(messageId);
      }
      return newSet;
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[600px] border border-border/50 rounded-lg bg-card/50">
      <div className="flex items-center justify-between p-4 border-b border-border/50">
        <div>
          <h3 className="font-semibold">Document Discussion</h3>
          <p className="text-xs text-muted-foreground">
            Collaborate with others • Use @beacon to ask questions
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Users className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">
            {participants.filter((p) => p.is_active).length} active
          </span>
        </div>
      </div>

      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {messages.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-muted-foreground">
                No messages yet. Start the conversation!
              </p>
              <p className="text-sm text-muted-foreground mt-2">
                Tip: Type <code className="bg-muted px-1 rounded">@beacon</code>{" "}
                to ask questions about this document
              </p>
            </div>
          ) : (
            // Only render top-level messages (replies are rendered within their parents)
            messages
              .filter((m) => !m.parent_message_id)
              .map((m) => renderMessage(m, false))
          )}

          {beaconThinking && (
            <div className="flex gap-3">
              <Avatar className="h-8 w-8 flex-shrink-0">
                <AvatarFallback className="bg-gradient-to-br from-primary to-accent text-primary-foreground">
                  <Sparkles className="h-4 w-4" />
                </AvatarFallback>
              </Avatar>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-semibold text-sm">Beacon AI</span>
                  <Badge
                    variant="secondary"
                    className="text-xs bg-primary/10 text-primary"
                  >
                    AI Assistant
                  </Badge>
                </div>
                <div className="rounded-lg p-3 bg-gradient-to-br from-primary/10 to-accent/10 border border-primary/20">
                  <div className="flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span className="text-sm">Analyzing document...</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      <div className="p-4 border-t border-border/50">
        {replyTo && (
          <div className="mb-2 p-2 bg-muted/50 rounded-lg flex items-center justify-between border-l-2 border-primary">
            <div className="flex-1">
              <span className="text-xs text-muted-foreground block">
                Replying to
              </span>
              <span className="text-sm font-medium">{replyTo.user_name}</span>
              <p className="text-xs text-muted-foreground truncate mt-0.5">
                {replyTo.content.substring(0, 50)}...
              </p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setReplyTo(null);
                setReplyPrefix("");
                setNewMessage("");
              }}
              className="h-6"
            >
              Cancel
            </Button>
          </div>
        )}

        {showSuggestions && userSuggestions.length > 0 && (
          <div className="mb-2 p-2 bg-popover border border-border rounded-lg shadow-lg max-h-40 overflow-y-auto">
            {userSuggestions.map((user) => (
              <button
                key={user.id}
                onClick={() => insertMention(user)}
                className="w-full flex items-center gap-2 p-2 hover:bg-muted rounded transition-colors"
              >
                <User className="h-4 w-4" />
                <div className="text-left">
                  <div className="text-sm font-medium">{user.name}</div>
                  <div className="text-xs text-muted-foreground">
                    {user.email}
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}

        <div className="flex gap-2">
          <Input
            ref={inputRef}
            value={newMessage}
            onChange={handleInputChange}
            onKeyPress={handleKeyPress}
            placeholder="Type a message... (@beacon for AI, @name to mention)"
            disabled={sending}
            className="flex-1"
          />
          <Button
            onClick={sendMessage}
            disabled={
              sending ||
              !newMessage.trim() ||
              (replyPrefix && newMessage.trim() === replyPrefix.trim())
            }
            className="neon-glow"
          >
            {sending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>
    </div>
  );
};
