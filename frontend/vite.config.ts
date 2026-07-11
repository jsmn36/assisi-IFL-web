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
  },
  build: {
    // Advanced Code Splitting with Manual Chunks
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules/react') || id.includes('react-dom') || id.includes('react-router-dom')) {
            return 'react-vendor';
          }
          if (id.includes('lucide-react') || id.includes('clsx') || id.includes('tailwind-merge')) {
            return 'ui-vendor';
          }
          if (id.includes('src/crm')) {
            return 'crm-feature';
          }
          if (id.includes('src/pages/AuditLogs') || id.includes('src/pages/ComplianceDashboard')) {
            return 'audit-feature';
          }
        },
      },
    },
    // Optimize performance settings
    chunkSizeWarningLimit: 1000,
    reportCompressedSize: true, // Report compressed size to help analyze builds
    sourcemap: true, // Useful for production debugging
  },
  // Development server configuration
  server: {
    port: 5173,
    host: true, // Enable listening on all interfaces (for mobile device testing)
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  // Ensure common dependencies are pre-bundled
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom', 'axios'],
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './vitest.setup.ts',
  },
})
