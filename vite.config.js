import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const buildTargets = {
  onboarding: {
    entry: "frontend/onboarding/main.jsx",
    fileName: "onboard.js",
    name: "AuthorOnboarding",
    outDir: "onboarding/static/onboarding/dist",
  },
  generation: {
    entry: "frontend/generation/main.jsx",
    fileName: "generation.js",
    name: "AuthorGeneration",
    outDir: "onboarding/static/generation/dist",
  },
};

export default defineConfig(({ command, mode }) => {
  const buildTarget = buildTargets[mode] || buildTargets.onboarding;

  return {
    define: command === "build"
      ? { "process.env.NODE_ENV": JSON.stringify("production") }
      : {},
    plugins: [react()],
    test: {
      environment: "jsdom",
      globals: true,
      setupFiles: ["./frontend/test/setup.js"],
    },
    server: {
      proxy: {
        "/authors": "http://127.0.0.1:8000",
        "/books": "http://127.0.0.1:8000",
        "/generate": "http://127.0.0.1:8000",
        "/genres": "http://127.0.0.1:8000",
        "/onboarding": "http://127.0.0.1:8000",
        "/website-briefs": "http://127.0.0.1:8000",
      },
    },
    build: {
      emptyOutDir: false,
      lib: {
        entry: buildTarget.entry,
        formats: ["iife"],
        name: buildTarget.name,
        fileName: () => buildTarget.fileName,
      },
      outDir: buildTarget.outDir,
    },
  };
});
