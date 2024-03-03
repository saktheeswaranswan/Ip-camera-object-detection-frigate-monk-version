/// <reference types="vitest" />
import path from "path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import monacoEditorPlugin from "vite-plugin-monaco-editor";

// https://vitejs.dev/config/
export default defineConfig({
  define: {
    "import.meta.vitest": "undefined",
  },
  server: {
    proxy: {
      "/api": {
        target: "http://192.168.5.4:5000",
        ws: true,
      },
      "/vod": {
        target: "http://192.168.5.4:5000",
      },
      "/clips": {
        target: "http://192.168.5.4:5000",
      },
      "/exports": {
        target: "http://192.168.5.4:5000",
      },
      "/ws": {
        target: "ws://192.168.5.4:5000",
        ws: true,
      },
      "/live": {
        target: "ws://192.168.5.4:5000",
        changeOrigin: true,
        ws: true,
      },
    },
  },
  plugins: [
    react(),
    monacoEditorPlugin.default({
      customWorkers: [{ label: "yaml", entry: "monaco-yaml/yaml.worker" }],
      languageWorkers: ["editorWorkerService"], // we don't use any of the default languages
    }),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  test: {
    environment: "jsdom",
    alias: {
      "testing-library": path.resolve(
        __dirname,
        "./__test__/testing-library.js",
      ),
    },
    setupFiles: ["./__test__/test-setup.ts"],
    includeSource: ["src/**/*.{js,jsx,ts,tsx}"],
    coverage: {
      reporter: ["text-summary", "text"],
    },
    mockReset: true,
    restoreMocks: true,
    globals: true,
  },
});
