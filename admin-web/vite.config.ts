/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
    dedupe: ['react', 'react-dom', 'react-router-dom'],
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules/react') || id.includes('react-dom') || id.includes('react-router-dom')) {
            return 'react-vendor';
          }
          if (id.includes('lucide-react') || id.includes('clsx') || id.includes('tailwind-merge')) {
            return 'ui-vendor';
          }
        },
      },
    },
    chunkSizeWarningLimit: 1000,
    reportCompressedSize: true,
    sourcemap: true,
  },
  server: {
    port: 3001,
    host: true,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/static': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom', 'axios'],
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './vitest.setup.ts',
  },
})
