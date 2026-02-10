import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";


// https://vitejs.dev/config/
//we can also use here build: { outDir: 'build' } to change build folder name
export default defineConfig({
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
    plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
