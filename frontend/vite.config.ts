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
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
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
