import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";


export default defineConfig(({ command }) => ({
  define: command === "build"
    ? { "process.env.NODE_ENV": JSON.stringify("production") }
    : {},
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./frontend/test/setup.js"],
  },
  build: {
    emptyOutDir: false,
    lib: {
      entry: "frontend/onboarding/main.jsx",
      formats: ["iife"],
      name: "AuthorOnboarding",
      fileName: () => "onboard.js",
    },
    outDir: "onboarding/static/onboarding",
  },
}));
