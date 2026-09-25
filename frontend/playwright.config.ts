import { defineConfig } from "@playwright/test"

/**
 * UAT E2E del modo en vivo (`US-6.3.10`): circuitos completos en navegador real, sin intervención.
 * Levanta backend y frontend en modo desarrollo (`StrictMode` activo, lección `US-ADJ-20`) o reutiliza
 * los que ya estén corriendo. Serial: todos los circuitos comparten la base local y la Comisión sembrada.
 * Uso: `npm run test:e2e` (desde `frontend/`).
 */
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  timeout: 180_000,
  expect: { timeout: 10_000 },
  retries: 0,
  globalSetup: "./e2e/soporte/sembrar.ts",
  globalTeardown: "./e2e/soporte/limpiar.ts",
  reporter: [
    ["list"],
    ["html", { outputFolder: "../quality/reports/uat/inc6/playwright-report", open: "never" }],
    ["json", { outputFile: "../quality/reports/uat/inc6/playwright-resultados.json" }],
  ],
  use: {
    baseURL: "http://localhost:5173",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  outputDir: "./test-results",
  webServer: [
    {
      command: "cd .. && .venv/bin/uvicorn src.app:app --port 8000",
      url: "http://localhost:8000/health",
      reuseExistingServer: true,
      timeout: 60_000,
    },
    {
      command: "npm run dev -- --port 5173 --strictPort",
      url: "http://localhost:5173",
      reuseExistingServer: true,
      timeout: 60_000,
    },
  ],
})
