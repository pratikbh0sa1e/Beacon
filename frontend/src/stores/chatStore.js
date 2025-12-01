import { create } from "zustand";
import { chatAPI } from "../services/api";
import { toast } from "sonner";

export const useChatStore = create((set, get) => ({
  // State
  sessions: [],
  currentSessionId: null,
  messages: [],
  loading: false,
  error: null,
  searchQuery: "",

  // ============================================================================
  // Session Management
  // ============================================================================

  /**
   * Fetch all sessions from backend
   */
  fetchSessions: async (params = {}) => {
    set({ loading: true, error: null });
    try {
      const response = await chatAPI.listSessions(params);
      const sessions = response.data.sessions.map((session) => ({
        id: session.session_id,
        title: session.title,
        threadId: session.thread_id,
        createdAt: session.created_at,
        updatedAt: session.updated_at,
        messageCount: session.message_count || 0,
        lastMessage: session.last_message || null,
      }));

      set({ sessions, loading: false });
      return sessions;
    } catch (error) {
      console.error("Error fetching sessions:", error);
      set({ error: error.message, loading: false });
      toast.error("Failed to load chat sessions");
      return [];
    }
  },

  /**
   * Create a new session
   */
  createSession: async (title = null) => {
    set({ loading: true, error: null });
    try {
      const response = await chatAPI.createSession(title);
      const newSession = {
        id: response.data.session_id,
        title: response.data.title,
        threadId: response.data.thread_id,
        createdAt: response.data.created_at,
        updatedAt: response.data.updated_at,
        messageCount: 0,
        lastMessage: null,
      };

      set((state) => ({
        sessions: [newSession, ...state.sessions],
        currentSessionId: newSession.id,
        messages: [],
        loading: false,
      }));

      // Save to localStorage for persistence
      localStorage.setItem("beacon-active-session", newSession.id.toString());

      return newSession.id;
    } catch (error) {
      console.error("Error creating session:", error);
      set({ error: error.message, loading: false });
      toast.error("Failed to create new chat");
      return null;
    }
  },

  /**
   * Load a session and its messages
   */
  loadSession: async (sessionId) => {
    set({ loading: true, error: null, currentSessionId: sessionId });
    try {
      const response = await chatAPI.getSessionMessages(sessionId);
      const messages = response.data.messages.map((msg) => ({
        id: msg.id,
        text: msg.content,
        isUser: msg.role === "user",
        citations: msg.citations || [],
        confidence: msg.confidence,
        timestamp: msg.created_at,
      }));

      set({ messages, loading: false });

      // Save to localStorage
      localStorage.setItem("beacon-active-session", sessionId.toString());

      return messages;
    } catch (error) {
      console.error("Error loading session:", error);
      set({ error: error.message, loading: false });
      toast.error("Failed to load chat history");
      return [];
    }
  },

  /**
   * Get current session
   */
  getCurrentSession: () => {
    const { sessions, currentSessionId } = get();
    return sessions.find((s) => s.id === currentSessionId);
  },

  /**
   * Send a message (calls backend and updates state)
   */
  sendMessage: async (question) => {
    const { currentSessionId } = get();

    // Add user message to UI immediately
    const userMessage = {
      id: Date.now(),
      text: question,
      isUser: true,
      timestamp: new Date().toISOString(),
    };

    set((state) => ({
      messages: [...state.messages, userMessage],
    }));

    try {
      // Call backend
      const response = await chatAPI.query(question, currentSessionId);

      // Add AI response to UI
      const aiMessage = {
        id: response.data.message_id,
        text: response.data.answer,
        isUser: false,
        citations: response.data.citations || [],
        confidence: response.data.confidence,
        timestamp: new Date().toISOString(),
      };

      set((state) => ({
        messages: [...state.messages, aiMessage],
        currentSessionId: response.data.session_id, // Update if new session was created
      }));

      // Refresh sessions list to update message count and last message
      get().fetchSessions();

      return aiMessage;
    } catch (error) {
      console.error("Error sending message:", error);
      toast.error("Failed to send message");

      // Remove user message on error
      set((state) => ({
        messages: state.messages.filter((m) => m.id !== userMessage.id),
      }));

      return null;
    }
  },

  /**
   * Delete a session
   */
  deleteSession: async (sessionId) => {
    try {
      await chatAPI.deleteSession(sessionId);

      set((state) => {
        const newSessions = state.sessions.filter((s) => s.id !== sessionId);
        const newCurrentId =
          state.currentSessionId === sessionId
            ? newSessions[0]?.id || null
            : state.currentSessionId;

        // If deleted current session, load the new current session
        if (newCurrentId && newCurrentId !== state.currentSessionId) {
          get().loadSession(newCurrentId);
        } else if (!newCurrentId) {
          // No sessions left, create a new one
          get().createSession();
        }

        return {
          sessions: newSessions,
          currentSessionId: newCurrentId,
        };
      });

      toast.success("Chat deleted");
    } catch (error) {
      console.error("Error deleting session:", error);
      toast.error("Failed to delete chat");
    }
  },

  /**
   * Rename a session
   */
  renameSession: async (sessionId, newTitle) => {
    try {
      await chatAPI.updateSessionTitle(sessionId, newTitle);

      set((state) => ({
        sessions: state.sessions.map((session) =>
          session.id === sessionId
            ? {
                ...session,
                title: newTitle,
                updatedAt: new Date().toISOString(),
              }
            : session
        ),
      }));

      toast.success("Chat renamed");
    } catch (error) {
      console.error("Error renaming session:", error);
      toast.error("Failed to rename chat");
    }
  },

  /**
   * Search sessions
   */
  searchSessions: async (query) => {
    set({ searchQuery: query, loading: true });

    if (!query.trim()) {
      // If empty query, fetch all sessions
      await get().fetchSessions();
      return;
    }

    try {
      const response = await chatAPI.searchSessions(query);
      const sessions = response.data.sessions.map((session) => ({
        id: session.session_id,
        title: session.title,
        threadId: session.thread_id,
        createdAt: session.created_at,
        updatedAt: session.updated_at,
        messageCount: session.message_count || 0,
        lastMessage: session.last_message || null,
      }));

      set({ sessions, loading: false });
    } catch (error) {
      console.error("Error searching sessions:", error);
      set({ loading: false });
      toast.error("Failed to search chats");
    }
  },

  /**
   * Initialize - load sessions and restore active session
   */
  initialize: async () => {
    // Fetch all sessions
    await get().fetchSessions();

    // Restore active session from localStorage
    const savedSessionId = localStorage.getItem("beacon-active-session");
    if (savedSessionId) {
      const sessionId = parseInt(savedSessionId);
      const session = get().sessions.find((s) => s.id === sessionId);
      if (session) {
        await get().loadSession(sessionId);
        return;
      }
    }

    // If no saved session or session not found, create new one
    const sessions = get().sessions;
    if (sessions.length > 0) {
      await get().loadSession(sessions[0].id);
    } else {
      await get().createSession();
    }
  },

  /**
   * Clear all state (for logout)
   */
  clearAll: () => {
    set({
      sessions: [],
      currentSessionId: null,
      messages: [],
      loading: false,
      error: null,
      searchQuery: "",
    });
    localStorage.removeItem("beacon-active-session");
  },
}));
