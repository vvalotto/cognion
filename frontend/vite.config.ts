import path from 'path'
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  // Proxy de desarrollo (US-6.3.10): con `VITE_API_BASE_URL=http://<IP>:5173/api` y `npm run dev -- --host`,
  // un celular en la red habla solo con Vite, que reenvía HTTP y WebSocket al backend local — sin pedidos a
  // otro origen, así que el CORS del backend (solo `localhost:5173`) no interviene. Sin la variable, no se usa.
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        ws: true,
        rewrite: (ruta) => ruta.replace(/^\/api/, ''),
      },
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    // Los circuitos E2E de Playwright (`e2e/`, US-6.3.10) no son de Vitest.
    exclude: ['**/node_modules/**', 'e2e/**'],
    // Margen ante carga ajena a Vitest en la máquina local (US-ADJ-53): con carga normal ningún
    // test se acerca a 5 s; solo cambia algo si un test se cuelga (falla a los 20 s).
    testTimeout: 20000,
    coverage: {
      provider: 'v8',
      // La tabla de cobertura sale aunque falle algún test (US-ADJ-53).
      reportOnFailure: true,
      thresholds: {
        lines: 80,
        functions: 80,
        branches: 80,
        statements: 80,
      },
    },
  },
})
