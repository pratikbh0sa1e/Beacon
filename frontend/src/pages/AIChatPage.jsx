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
} from "lucide-react";
import { chatAPI, voiceAPI } from "../services/api";
import { PageHeader } from "../components/common/PageHeader";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardContent } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { toast } from "sonner";
import "highlight.js/styles/github-dark.css";

const Message = ({ message, isUser, onCitationClick }) => (
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
                  <ol className="mb-2 ml-4 list-decimal text-sm">{children}</ol>
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
                  <td className="border border-border px-3 py-2">{children}</td>
                ),
              }}
            >
              {message.text}
            </ReactMarkdown>
          </div>
        )}
      </div>
      {message.confidence && (
        <div className="flex items-center gap-2 mt-2 px-2">
          <Badge variant="outline" className="text-xs">
            Confidence: {(message.confidence * 100).toFixed(0)}%
          </Badge>
        </div>
      )}
      {message.citations && message.citations.length > 0 && (
        <div className="mt-3 space-y-2">
          <p className="text-xs text-muted-foreground px-2">Sources:</p>
          {message.citations.map((citation, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.1 }}
              onClick={() => onCitationClick(citation.document_id)}
              className="glass-card border-border/50 p-3 rounded-lg cursor-pointer hover:bg-accent/5 transition-colors"
            >
              <div className="flex items-start gap-2">
                <FileText className="h-4 w-4 text-primary flex-shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">
                    {citation.source}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Page {citation.page_number}
                  </p>
                </div>
                <ExternalLink className="h-3 w-3 text-muted-foreground flex-shrink-0 mt-0.5" />
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
    {isUser && (
      <div className="h-8 w-8 rounded-full bg-accent/10 flex items-center justify-center flex-shrink-0">
        <User className="h-5 w-5 text-accent" />
      </div>
    )}
  </motion.div>
);

export const AIChatPage = () => {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Hello! I'm the **BEACON AI Assistant**. Ask me anything about your documents, and I'll help you find the information you need. You can type your question or use voice input! 🎤",
      isUser: false,
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioChunks, setAudioChunks] = useState([]);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Regular non-streaming handler (current implementation)
  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = {
      id: Date.now(),
      text: input,
      isUser: true,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const response = await chatAPI.query(input);
      const { answer, citations, confidence } = response.data;

      const aiMessage = {
        id: Date.now() + 1,
        text: answer,
        isUser: false,
        citations: citations || [],
        confidence: confidence || 0,
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      console.error("Chat error:", error);
      const errorMessage = {
        id: Date.now() + 1,
        text: "I apologize, but I encountered an error processing your request. Please try again.",
        isUser: false,
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
      toast.error("Failed to get AI response");
    } finally {
      setLoading(false);
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
        await handleVoiceQuery(audioBlob);
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

  const handleVoiceQuery = async (audioFile) => {
    setLoading(true);

    try {
      // Show user message indicating voice input
      const userMessage = {
        id: Date.now(),
        text: "🎤 Voice message...",
        isUser: true,
      };
      setMessages((prev) => [...prev, userMessage]);

      // Send to voice API
      const response = await voiceAPI.query(audioFile);
      const { transcription, answer, citations, confidence, language } =
        response.data;

      // Update user message with transcription
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === userMessage.id
            ? { ...msg, text: `🎤 "${transcription}"` }
            : msg
        )
      );

      // Add AI response
      const aiMessage = {
        id: Date.now() + 1,
        text: answer,
        isUser: false,
        citations: citations || [],
        confidence: confidence || 0,
        language: language,
      };

      setMessages((prev) => [...prev, aiMessage]);
      toast.success("Voice query processed successfully");
    } catch (error) {
      console.error("Voice query error:", error);
      const errorMessage = {
        id: Date.now() + 1,
        text: "I apologize, but I encountered an error processing your voice message. Please try again or type your question.",
        isUser: false,
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
      toast.error(
        error.response?.data?.detail || "Failed to process voice query"
      );
    } finally {
      setLoading(false);
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
    <div className="h-[calc(100vh-12rem)] flex flex-col space-y-6">
      <PageHeader
        title="AI Assistant"
        description="Ask questions about your documents and get intelligent answers"
        icon={Bot}
      />

      <Card className="glass-card border-border/50 flex-1 flex flex-col overflow-hidden">
        <CardContent className="p-6 flex-1 flex flex-col min-h-0">
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
              {streamingMessage && (
                <Message
                  key={streamingMessage.id}
                  message={streamingMessage}
                  isUser={false}
                  onCitationClick={handleCitationClick}
                />
              )}
            </AnimatePresence>
            {loading && !streamingMessage && (
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
                accept="audio/*,.mp3,.wav,.m4a,.ogg,.flac"
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
  );
};
