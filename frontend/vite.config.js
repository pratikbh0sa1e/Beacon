// import { defineConfig } from 'vite'
// import react from '@vitejs/plugin-react'

// // https://vite.dev/config/
// export default defineConfig({
//   plugins: [react()],
// })
import path from "path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import { fileURLToPath } from "url"; // <--- Import this

// Fix for __dirname in ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  // THIS IS THE FIX FOR CORS:
  server: {
    port: 3000,
    open: true,
    // Enable client-side routing (SPA fallback)
    historyApiFallback: true,
  },
  // Keep this safety net just in case
  define: {
    "process.env": {},
  },
});
