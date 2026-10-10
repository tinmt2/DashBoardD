import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': new URL('./src', import.meta.url).pathname,
    },
  },
  base: './', // critical for Electron - use relative paths
  server: {
    port: 5174,
    strictPort: true,
    host: true,
  },
  build: {
    outDir: 'dist',
    chunkSizeWarningLimit: 800,
  },
})
