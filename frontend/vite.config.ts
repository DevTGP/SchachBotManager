import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// The dev server passes /api on to a local API, as the frontend container does in the stack.
const apiTarget = process.env.SBM_API_URL ?? "http://127.0.0.1:5000";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { "/api": apiTarget },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["src/test/setup.ts"],
  },
});
