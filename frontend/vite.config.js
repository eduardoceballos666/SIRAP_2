import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import { fileURLToPath, URL } from 'node:url'

// En desarrollo, /api se reenvía a FastAPI (uvicorn api.main:app --port 8000).
export default defineConfig({
  plugins: [vue(), tailwindcss()],
  resolve: { alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) } },
  server: {
    port: 5173,
    proxy: { '/api': { target: process.env.SIRAP_API_URL || 'http://localhost:8000', changeOrigin: true } },
  },
  build: { chunkSizeWarningLimit: 1200 },
})
