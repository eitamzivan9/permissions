import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Defaults to the same-host assumption CLOSED_NETWORK_MIGRATION.md documents as
// current behavior. Overridden via VITE_BACKEND_URL when frontend and backend are on
// different hosts — e.g. inside docker-compose, where the backend is reachable at
// http://backend:8000, not 127.0.0.1.
const backendTarget = process.env.VITE_BACKEND_URL ?? 'http://127.0.0.1:8000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: true,
    proxy: {
      '/api': {
        target: backendTarget,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
