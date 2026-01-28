import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

// https://vitejs.dev/config/
//we can also use here build: { outDir: 'build' } to change build folder name
export default defineConfig(({ mode }) => ({
  build: {
    outDir: 'build'
  },
  server: {
      port: 3000,
    host: '0.0.0.0',
    allowedHosts: true
  },
// export default defineConfig(({ mode }) => ({
//   server: {
//     host: "::",
//     port: 8080,
//   },
  plugins: [react(), mode === "development" && componentTagger()].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
}));
