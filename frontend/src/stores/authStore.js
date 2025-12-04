// stores/authStore.js - Complete Auth Store with Session Management

import { create } from "zustand";
import { persist } from "zustand/middleware";

const SESSION_TIMEOUT = 24 * 60 * 60 * 1000; // 24 hours in milliseconds
const WARNING_TIME = 10 * 60 * 1000; // 10 minutes before timeout

// Helper function to decode JWT
const decodeToken = (token) => {
  try {
    const base64Url = token.split(".")[1];
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join("")
    );
    return JSON.parse(jsonPayload);
  } catch (error) {
    console.error("Error decoding token:", error);
    return null;
  }
};

export const useAuthStore = create(
  persist(
    (set, get) => ({
      // State
      token: null,
      user: null,
      isAuthenticated: false,
      sessionTimer: null,
      warningTimer: null,
      lastActivity: Date.now(),
      showSessionWarning: false,

      // ✅ Set authentication (called after login)
      setAuth: (token, user) => {
        set({
          token,
          user,
          isAuthenticated: true,
          lastActivity: Date.now(),
          showSessionWarning: false,
        });

        // Store in localStorage
        localStorage.setItem("token", token);
        localStorage.setItem("user", JSON.stringify(user));

        // Start session timers
        get().startSessionTimers();
      },

      // ✅ Logout
      logout: (reason) => {
        const state = get();
        state.clearSessionTimers();

        set({
          token: null,
          user: null,
          isAuthenticated: false,
          sessionTimer: null,
          warningTimer: null,
          lastActivity: null,
          showSessionWarning: false,
        });

        // Clear localStorage
        localStorage.removeItem("token");
        localStorage.removeItem("user");

        // Show toast if reason provided
        if (reason && typeof window !== "undefined") {
          import("sonner").then(({ toast }) => {
            toast.warning(reason);
          });
        }
      },

      // ✅ Update user data
      updateUser: (userData) => {
        set((state) => {
          const updatedUser = { ...state.user, ...userData };
          localStorage.setItem("user", JSON.stringify(updatedUser));
          return { user: updatedUser };
        });
      },

      // ✅ Refresh user data from API
      refreshUser: async () => {
        const token = get().token;
        if (!token) return;

        try {
          const response = await fetch(
            `${
              import.meta.env.VITE_API_URL || "http://localhost:8000"
            }/auth/me`,
            {
              headers: {
                Authorization: `Bearer ${token}`,
              },
            }
          );

          if (response.ok) {
            const userData = await response.json();
            get().setUser(userData);
          }
        } catch (error) {
          console.error("Failed to refresh user data:", error);
        }
      },

      // ✅ Set user data
      setUser: (user) => {
        set({ user });
        localStorage.setItem("user", JSON.stringify(user));
      },

      // ✅ Check if user is approved
      isApproved: () => {
        const user = get().user;
        return user?.approved === true;
      },

      // ✅ Check if user has specific role
      hasRole: (role) => {
        const user = get().user;
        return user?.role === role;
      },

      // ✅ Check if user has any of the roles
      hasAnyRole: (roles) => {
        const user = get().user;
        return roles.includes(user?.role);
      },

      // ✅ Update last activity timestamp
      updateActivity: () => {
        const state = get();
        if (state.isAuthenticated) {
          set({ lastActivity: Date.now(), showSessionWarning: false });
          // Restart timers
          state.clearSessionTimers();
          state.startSessionTimers();
        }
      },

      // ✅ Start session timeout timers
      startSessionTimers: () => {
        const state = get();

        // Clear existing timers
        state.clearSessionTimers();

        // Warning timer (5 minutes before timeout)
        const warningTimer = setTimeout(() => {
          set({ showSessionWarning: true });
        }, SESSION_TIMEOUT - WARNING_TIME);

        // Logout timer (after full timeout)
        const sessionTimer = setTimeout(() => {
          state.logout("Session expired due to inactivity");
        }, SESSION_TIMEOUT);

        set({ sessionTimer, warningTimer });
      },

      // ✅ Clear session timers
      clearSessionTimers: () => {
        const { sessionTimer, warningTimer } = get();
        if (sessionTimer) clearTimeout(sessionTimer);
        if (warningTimer) clearTimeout(warningTimer);
        set({ sessionTimer: null, warningTimer: null });
      },

      // ✅ Extend session (when user clicks "Stay Logged In")
      extendSession: () => {
        get().updateActivity();
        set({ showSessionWarning: false });
      },

      // ✅ Initialize auth from storage
      initAuth: () => {
        const token = localStorage.getItem("token");
        const userStr = localStorage.getItem("user");

        if (token && userStr) {
          try {
            // Check if token is expired
            const decoded = decodeToken(token);
            if (!decoded) {
              get().logout();
              return;
            }

            const now = Date.now() / 1000;
            if (decoded.exp && decoded.exp < now) {
              get().logout("Session expired");
              return;
            }

            const user = JSON.parse(userStr);
            set({
              token,
              user,
              isAuthenticated: true,
              lastActivity: Date.now(),
            });

            // Start session timers
            get().startSessionTimers();

            // Refresh user data from API to get latest info (including name)
            get().refreshUser();
          } catch (error) {
            console.error("Auth initialization error:", error);
            get().logout();
          }
        }
      },
    }),
    {
      name: "beacon-auth",
      partialize: (state) => ({
        token: state.token,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        lastActivity: state.lastActivity,
      }),
    }
  )
);
