import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api/metrics': { target: 'http://localhost:8001', rewrite: (p) => p.replace(/^\/api\/metrics/, '') },
      '/api/alerts':  { target: 'http://localhost:8002', rewrite: (p) => p.replace(/^\/api\/alerts/, '')  },
      '/api/cost':    { target: 'http://localhost:8003', rewrite: (p) => p.replace(/^\/api\/cost/, '')    },
    },
  },
  build: { outDir: 'dist', sourcemap: false },
})
