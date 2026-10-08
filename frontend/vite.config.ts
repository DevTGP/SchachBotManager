import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// The dev server passes /api on to a local API and the game socket to a local gateway, as the
// frontend container does in the stack (E112).
const apiTarget = process.env.SBM_API_URL ?? "http://127.0.0.1:5000";
const gatewayTarget = process.env.SBM_GATEWAY_URL ?? "ws://127.0.0.1:8001";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api/v1/play/socket": { target: gatewayTarget, ws: true },
      "/api": apiTarget,
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["src/test/setup.ts"],
  },
});
