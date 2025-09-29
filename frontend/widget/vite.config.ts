import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    lib: {
  entry: "./src/mount.tsx",   // <— was .ts
  name: "RoomMatcher",
  fileName: "room-matcher-widget",
  formats: ["umd"]
},

    rollupOptions: {
      external: ["react", "react-dom"],
      output: {
        globals: {
          react: "React",
          "react-dom": "ReactDOM"
        }
      }
    }
  }
});
