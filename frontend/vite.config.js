import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Proxy API calls during local dev so you don't need CORS workarounds
      "/upload": "http://localhost:8000",
      "/query": "http://localhost:8000",
      "/health": "http://localhost:8000",
      "/docs-list": "http://localhost:8000",
    },
  },
});
