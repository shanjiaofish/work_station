import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',            // 👈 allow external access
    port: 5173,                 // 👈 bind to port 5173
    allowedHosts: [
      'jog150.synology.me',     // 👈 your domain or DDNS hostname
      'localhost',
      '127.0.0.1'
    ],
    cors: true,                 // optional: allow API calls from other origins
  },
})
