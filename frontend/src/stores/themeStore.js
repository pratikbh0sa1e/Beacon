// stores/themeStore.js - Theme Management Store

import { create } from "zustand";
import { persist } from "zustand/middleware";

export const useThemeStore = create(
  persist(
    (set, get) => ({
      theme: "dark", // 'light', 'dark', or 'system'

      setTheme: (theme) => {
        set({ theme });
        applyTheme(theme);
      },

      toggleTheme: () => {
        const current = get().theme;
        const next = current === "dark" ? "light" : "dark";
        set({ theme: next });
        applyTheme(next);
      },

      initTheme: () => {
        const theme = get().theme;
        applyTheme(theme);
      },
    }),
    {
      name: "beacon-theme",
    }
  )
);

// Apply theme to document
function applyTheme(theme) {
  if (typeof window === "undefined") return;

  const root = document.documentElement;

  if (theme === "system") {
    const systemTheme = window.matchMedia("(prefers-color-scheme: dark)")
      .matches
      ? "dark"
      : "light";
    root.classList.remove("light", "dark");
    root.classList.add(systemTheme);
  } else {
    root.classList.remove("light", "dark");
    root.classList.add(theme);
  }
}

// Listen for system theme changes
if (typeof window !== "undefined") {
  window
    .matchMedia("(prefers-color-scheme: dark)")
    .addEventListener("change", (e) => {
      const store = useThemeStore.getState();
      if (store.theme === "system") {
        applyTheme("system");
      }
    });
}
