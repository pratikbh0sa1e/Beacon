import { create } from "zustand";
import { persist } from "zustand/middleware";

export const useChatStore = create(
  persist(
    (set, get) => ({
      // Chat sessions
      sessions: [],
      currentSessionId: null,

      // Create a new session
      createSession: () => {
        const newSession = {
          id: Date.now().toString(),
          title: "New Chat",
          messages: [
            {
              id: 1,
              text: "Hello! I'm the **BEACON AI Assistant**. Ask me anything about your documents, and I'll help you find the information you need.",
              isUser: false,
            },
          ],
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        };

        set((state) => ({
          sessions: [newSession, ...state.sessions],
          currentSessionId: newSession.id,
        }));

        return newSession.id;
      },

      // Load a session
      loadSession: (sessionId) => {
        const session = get().sessions.find((s) => s.id === sessionId);
        if (session) {
          set({ currentSessionId: sessionId });
          return session.messages;
        }
        return null;
      },

      // Get current session
      getCurrentSession: () => {
        const { sessions, currentSessionId } = get();
        return sessions.find((s) => s.id === currentSessionId);
      },

      // Add message to current session
      addMessage: (message) => {
        const { currentSessionId } = get();
        if (!currentSessionId) return;

        set((state) => ({
          sessions: state.sessions.map((session) =>
            session.id === currentSessionId
              ? {
                  ...session,
                  messages: [...session.messages, message],
                  updatedAt: new Date().toISOString(),
                  // Update title based on first user message
                  title:
                    session.messages.length === 1 && message.isUser
                      ? message.text.slice(0, 50) +
                        (message.text.length > 50 ? "..." : "")
                      : session.title,
                }
              : session
          ),
        }));
      },

      // Update messages in current session
      setMessages: (messages) => {
        const { currentSessionId } = get();
        if (!currentSessionId) return;

        set((state) => ({
          sessions: state.sessions.map((session) =>
            session.id === currentSessionId
              ? {
                  ...session,
                  messages,
                  updatedAt: new Date().toISOString(),
                }
              : session
          ),
        }));
      },

      // Delete a session
      deleteSession: (sessionId) => {
        set((state) => {
          const newSessions = state.sessions.filter((s) => s.id !== sessionId);
          const newCurrentId =
            state.currentSessionId === sessionId
              ? newSessions[0]?.id || null
              : state.currentSessionId;

          return {
            sessions: newSessions,
            currentSessionId: newCurrentId,
          };
        });
      },

      // Rename a session
      renameSession: (sessionId, newTitle) => {
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
      },

      // Clear all sessions
      clearAllSessions: () => {
        set({ sessions: [], currentSessionId: null });
      },

      // Initialize with a default session if none exists
      initializeSession: () => {
        const { sessions, currentSessionId } = get();
        if (sessions.length === 0 || !currentSessionId) {
          get().createSession();
        }
      },
    }),
    {
      name: "beacon-chat-history",
      partialize: (state) => ({
        sessions: state.sessions,
        currentSessionId: state.currentSessionId,
      }),
    }
  )
);
