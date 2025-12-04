import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import {
  Send,
  Bot,
  User,
  Loader2,
  FileText,
  AlertCircle,
  ExternalLink,
  Mic,
  MicOff,
  Upload,
  Menu,
  ChevronDown,
  ChevronUp,
  CheckCircle,
  Clock,
  XCircle,
} from "lucide-react";
import { useChatStore } from "../stores/chatStore";
import { ChatSidebar } from "../components/chat/ChatSidebar";
import { chatAPI, voiceAPI } from "../services/api";
import { PageHeader } from "../components/common/PageHeader";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardContent } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { toast } from "sonner";
import "highlight.js/styles/github-dark.css";

// Helper function to get approval status icon and color
const getApprovalStatusIcon = (status) => {
  switch (status) {
    case "approved":
      return {
        icon: CheckCircle,
        className: "text-green-600 dark:text-green-400",
        title: "Approved",
      };
    case "pending":
    case "under_review":
      return {
        icon: Clock,
        className: "text-yellow-600 dark:text-yellow-400",
        title: "Pending Review",
      };
    case "rejected":
    case "changes_requested":
      return {
        icon: XCircle,
        className: "text-red-600 dark:text-red-400",
        title: "Rejected",
      };
    case "draft":
      return {
        icon: FileText,
        className: "text-gray-600 dark:text-gray-400",
        title: "Draft",
      };
    default:
      return null;
  }
};

const Message = ({ message, isUser, onCitationClick }) => {
  const [showAllCitations, setShowAllCitations] = useState(false);
  const MAX_VISIBLE_CITATIONS = 3;

  const citations = message.citations || [];
  const hasManyCitations = citations.length > MAX_VISIBLE_CITATIONS;
  const visibleCitations = showAllCitations
    ? citations
    : citations.slice(0, MAX_VISIBLE_CITATIONS);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}
    >
      {!isUser && (
        <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
          <Bot className="h-5 w-5 text-primary" />
        </div>
      )}
      <div className={`max-w-[80%] ${isUser ? "order-first" : ""}`}>
        <div
          className={`rounded-2xl px-4 py-3 ${
            isUser
              ? "bg-primary text-primary-foreground"
              : "glass-card border-border/50"
          }`}
        >
          {isUser ? (
            <p className="text-sm leading-relaxed whitespace-pre-wrap">
              {message.text}
            </p>
          ) : (
            <div className="prose prose-sm dark:prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-muted prose-pre:text-foreground">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeHighlight]}
                components={{
                  p: ({ children }) => (
                    <p className="mb-2 last:mb-0 text-sm leading-relaxed">
                      {children}
                    </p>
                  ),
                  ul: ({ children }) => (
                    <ul className="mb-2 ml-4 list-disc text-sm">{children}</ul>
                  ),
                  ol: ({ children }) => (
                    <ol className="mb-2 ml-4 list-decimal text-sm">
                      {children}
                    </ol>
                  ),
                  li: ({ children }) => (
                    <li className="mb-1 text-sm">{children}</li>
                  ),
                  code: ({ inline, children, ...props }) =>
                    inline ? (
                      <code
                        className="bg-muted px-1.5 py-0.5 rounded text-xs font-mono"
                        {...props}
                      >
                        {children}
                      </code>
                    ) : (
                      <code
                        className="block bg-muted p-3 rounded-lg text-xs font-mono overflow-x-auto"
                        {...props}
                      >
                        {children}
                      </code>
                    ),
                  pre: ({ children }) => (
                    <pre className="bg-muted p-3 rounded-lg overflow-x-auto mb-2">
                      {children}
                    </pre>
                  ),
                  h1: ({ children }) => (
                    <h1 className="text-lg font-bold mb-2">{children}</h1>
                  ),
                  h2: ({ children }) => (
                    <h2 className="text-base font-bold mb-2">{children}</h2>
                  ),
                  h3: ({ children }) => (
                    <h3 className="text-sm font-bold mb-2">{children}</h3>
                  ),
                  blockquote: ({ children }) => (
                    <blockquote className="border-l-4 border-primary/50 pl-4 italic my-2 text-sm">
                      {children}
                    </blockquote>
                  ),
                  a: ({ children, href }) => (
                    <a
                      href={href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline"
                    >
                      {children}
                    </a>
                  ),
                  table: ({ children }) => (
                    <div className="overflow-x-auto my-2">
                      <table className="min-w-full border-collapse border border-border text-sm">
                        {children}
                      </table>
                    </div>
                  ),
                  th: ({ children }) => (
                    <th className="border border-border px-3 py-2 bg-muted font-semibold text-left">
                      {children}
                    </th>
                  ),
                  td: ({ children }) => (
                    <td className="border border-border px-3 py-2">
                      {children}
                    </td>
                  ),
                }}
              >
                {message.text}
              </ReactMarkdown>
            </div>
          )}
        </div>
        {/* Confidence and Sources - Pill Style */}
        <div className="flex flex-wrap items-center gap-2 mt-2 px-2">
          {message.confidence && (
            <Badge variant="outline" className="text-xs">
              Confidence: {message.confidence}%
            </Badge>
          )}

          {citations.length > 0 && (
            <>
              {/* Show visible citation pills */}
              {visibleCitations.map((citation, idx) => {
                const statusInfo = getApprovalStatusIcon(
                  citation.approval_status
                );
                const StatusIcon = statusInfo?.icon;

                return (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: idx * 0.05 }}
                  >
                    <Badge
                      variant="secondary"
                      className="text-xs cursor-pointer hover:bg-accent transition-colors max-w-[200px] group"
                      onClick={() => onCitationClick(citation.document_id)}
                      title={`${citation.source}${
                        citation.page_number
                          ? ` - Page ${citation.page_number}`
                          : ""
                      }${statusInfo ? ` - ${statusInfo.title}` : ""}`}
                    >
                      <FileText className="h-3 w-3 mr-1 flex-shrink-0" />
                      <span className="truncate">
                        {citation.source.length > 20
                          ? citation.source.substring(0, 20) + "..."
                          : citation.source}
                      </span>
                      {citation.page_number && (
                        <span className="ml-1 text-[10px] opacity-70">
                          p.{citation.page_number}
                        </span>
                      )}
                      {/* Approval Status Icon */}
                      {StatusIcon && (
                        <StatusIcon
                          className={`h-3 w-3 ml-1 flex-shrink-0 ${statusInfo.className}`}
                          title={statusInfo.title}
                        />
                      )}
                      <ExternalLink className="h-2.5 w-2.5 ml-1 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </Badge>
                  </motion.div>
                );
              })}

              {/* Show all toggle button */}
              {hasManyCitations && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowAllCitations(!showAllCitations)}
                  className="h-6 px-2 text-[10px] text-primary hover:text-primary"
                >
                  {showAllCitations ? (
                    <>
                      Show less <ChevronUp className="h-3 w-3 ml-0.5" />
                    </>
                  ) : (
                    <>
                      +{citations.length - MAX_VISIBLE_CITATIONS} more{" "}
                      <ChevronDown className="h-3 w-3 ml-0.5" />
                    </>
                  )}
                </Button>
              )}
            </>
          )}
        </div>
      </div>
      {isUser && (
        <div className="h-8 w-8 rounded-full bg-accent/10 flex items-center justify-center flex-shrink-0">
          <User className="h-5 w-5 text-accent" />
        </div>
      )}
    </motion.div>
  );
};

export const AIChatPage = () => {
  const navigate = useNavigate();
  const [input, setInput] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioChunks, setAudioChunks] = useState([]);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const inputRef = useRef(null);

  // Sidebar toggle state with localStorage persistence
  const [isSidebarOpen, setIsSidebarOpen] = useState(() => {
    const saved = localStorage.getItem("chatSidebarOpen");
    return saved !== null ? JSON.parse(saved) : true;
  });

  // Use chat store for session management
  const {
    messages,
    currentSessionId,
    loading,
    sendMessage,
    createSession,
    fetchSessions,
    clearCurrentSession,
  } = useChatStore();

  // Initialize chat store on mount and show welcome message if no session
  useEffect(() => {
    const initializeChat = async () => {
      await fetchSessions();
      // If no current session and no messages, show welcome message
      if (!currentSessionId && messages.length === 0) {
        clearCurrentSession();
      }
    };
    initializeChat();
  }, []);

  // Save sidebar state to localStorage
  useEffect(() => {
    localStorage.setItem("chatSidebarOpen", JSON.stringify(isSidebarOpen));
  }, [isSidebarOpen]);

  // Toggle sidebar function
  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
    // Focus input after messages update (after AI response)
    if (!loading && messages.length > 0) {
      inputRef.current?.focus();
    }
  }, [messages, loading]);

  // Send message using chat store
  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const messageText = input;
    setInput("");

    try {
      // If no current session, create one
      if (!currentSessionId) {
        await createSession(messageText.substring(0, 50));
      }

      // Send message through chat store
      await sendMessage(messageText);
    } catch (error) {
      console.error("Chat error:", error);
      toast.error("Failed to send message");
    }
  };

  // Voice recording handlers
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunks.push(e.data);
        }
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(chunks, { type: "audio/webm" });
        // Convert Blob to File for backend compatibility
        const audioFile = new File([audioBlob], "recording.webm", {
          type: "audio/webm",
        });
        await handleVoiceQuery(audioFile);
        stream.getTracks().forEach((track) => track.stop());
      };

      recorder.start();
      setMediaRecorder(recorder);
      setAudioChunks(chunks);
      setIsRecording(true);
      toast.info("Recording... Click again to stop");
    } catch (error) {
      console.error("Error accessing microphone:", error);
      toast.error("Could not access microphone. Please check permissions.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state === "recording") {
      mediaRecorder.stop();
      setIsRecording(false);
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      handleVoiceQuery(file);
    }
  };

  const [isTranscribing, setIsTranscribing] = useState(false);

  const handleVoiceQuery = async (audioFile) => {
    setIsTranscribing(true);

    try {
      // Send to voice API
      const response = await voiceAPI.query(audioFile);
      const { transcription } = response.data;

      setIsTranscribing(false);

      // Auto-send the transcription
      if (!currentSessionId) {
        await createSession(transcription.substring(0, 50));
      }
      await sendMessage(transcription);
    } catch (error) {
      setIsTranscribing(false);
      console.error("Voice query error:", error);
      toast.error(
        error.response?.data?.detail || "Failed to process voice query"
      );
    }
  };

  // Streaming handler (for future implementation)
  // Uncomment and use this when backend supports streaming
  /*
  const handleSendStreaming = async () => {
    if (!input.trim() || loading) return;

    const userMessage = {
      id: Date.now(),
      text: input,
      isUser: true,
    };

    setMessages((prev) => [...prev, userMessage]);
    const currentInput = input;
    setInput("");
    setLoading(true);

    const streamingMsgId = Date.now() + 1;
    setStreamingMessage({
      id: streamingMsgId,
      text: "",
      isUser: false,
      citations: [],
      confidence: 0,
    });

    try {
      // Example streaming implementation with fetch
      const response = await fetch(`${import.meta.env.VITE_API_URL}/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({ query: currentInput }),
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedText = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = JSON.parse(line.slice(6));
            
            if (data.type === "token") {
              accumulatedText += data.content;
              setStreamingMessage((prev) => ({
                ...prev,
                text: accumulatedText,
              }));
            } else if (data.type === "complete") {
              setMessages((prev) => [
                ...prev,
                {
                  id: streamingMsgId,
                  text: accumulatedText,
                  isUser: false,
                  citations: data.citations || [],
                  confidence: data.confidence || 0,
                },
              ]);
              setStreamingMessage(null);
            }
          }
        }
      }
    } catch (error) {
      console.error("Streaming error:", error);
      const errorMessage = {
        id: streamingMsgId,
        text: "I apologize, but I encountered an error processing your request. Please try again.",
        isUser: false,
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
      setStreamingMessage(null);
      toast.error("Failed to get AI response");
    } finally {
      setLoading(false);
    }
  };
  */

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleCitationClick = (documentId) => {
    window.open(`/documents/${documentId}`, "_blank");
  };

  return (
    <div className="h-[calc(100vh-6rem)] flex flex-col space-y-6 pb-6">
      <PageHeader
        title="AI Assistant"
        description="Ask questions about your documents and get intelligent answers"
        icon={Bot}
      />

      <div className="flex-1 flex gap-4 min-h-0 overflow-hidden">
        {/* Sidebar - Collapsible */}
        <AnimatePresence>
          {isSidebarOpen && (
            <motion.div
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 320, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ duration: 0.3, ease: "easeInOut" }}
              className="flex-shrink-0 overflow-hidden"
            >
              <Card className="glass-card border-border/50 h-full w-80">
                <ChatSidebar />
              </Card>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Main Chat Area */}
        <Card className="glass-card border-border/50 flex-1 flex flex-col overflow-hidden">
          <CardContent className="p-6 flex-1 flex flex-col min-h-0">
            {/* Toggle Button */}
            <div className="flex items-center gap-2 mb-4">
              <Button
                onClick={toggleSidebar}
                variant="outline"
                size="sm"
                className="flex items-center gap-2"
                title={
                  isSidebarOpen ? "Hide chat history" : "Show chat history"
                }
              >
                <Menu className="h-4 w-4" />
                <span className="text-xs">
                  {isSidebarOpen ? "Hide History" : "Show History"}
                </span>
              </Button>
            </div>
            <div className="flex-1 overflow-y-auto min-h-0 space-y-6 mb-4 scrollbar-hide">
              <AnimatePresence>
                {messages.map((message) => (
                  <Message
                    key={message.id}
                    message={message}
                    isUser={message.isUser}
                    onCitationClick={handleCitationClick}
                  />
                ))}
              </AnimatePresence>
              {isTranscribing && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex gap-3 justify-end"
                >
                  <div className="bg-primary text-primary-foreground rounded-2xl px-4 py-3 order-first">
                    <div className="flex items-center gap-2">
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{
                          duration: 1,
                          repeat: Infinity,
                          ease: "linear",
                        }}
                      >
                        <Loader2 className="h-4 w-4" />
                      </motion.div>
                      <span className="text-sm">Transcribing...</span>
                    </div>
                  </div>
                  <div className="h-8 w-8 rounded-full bg-accent/10 flex items-center justify-center flex-shrink-0">
                    <User className="h-5 w-5 text-accent" />
                  </div>
                </motion.div>
              )}
              {loading && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex gap-3"
                >
                  <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <Bot className="h-5 w-5 text-primary" />
                  </div>
                  <div className="glass-card border-border/50 rounded-2xl px-4 py-3">
                    <div className="flex items-center gap-2">
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{
                          duration: 1,
                          repeat: Infinity,
                          ease: "linear",
                        }}
                      >
                        <Loader2 className="h-4 w-4 text-primary" />
                      </motion.div>
                      <span className="text-sm text-muted-foreground">
                        Thinking...
                      </span>
                    </div>
                  </div>
                </motion.div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <div className="border-t border-border/40 pt-4">
              <div className="flex gap-2">
                <Input
                  ref={inputRef}
                  placeholder="Ask me anything about your documents..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  disabled={loading}
                  className="flex-1"
                />
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileUpload}
                  accept="audio/*,.mp3,.wav,.m4a,.ogg,.flac,.webm"
                  className="hidden"
                />
                <Button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={loading}
                  variant="outline"
                  title="Upload audio file"
                >
                  <Upload className="h-4 w-4" />
                </Button>
                <Button
                  onClick={toggleRecording}
                  disabled={loading}
                  variant={isRecording ? "destructive" : "outline"}
                  title={isRecording ? "Stop recording" : "Start recording"}
                >
                  {isRecording ? (
                    <MicOff className="h-4 w-4" />
                  ) : (
                    <Mic className="h-4 w-4" />
                  )}
                </Button>
                <Button
                  onClick={handleSend}
                  disabled={!input.trim() || loading}
                  className="neon-glow"
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
              <p className="text-xs text-muted-foreground mt-2 flex items-center gap-1">
                <AlertCircle className="h-3 w-3" />
                AI responses may not always be accurate. Verify important
                information. Use 🎤 for voice queries.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
