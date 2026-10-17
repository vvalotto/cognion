# Plan de Implementación — US-8.1.2

| # | Tarea | Archivo |
|---|-------|---------|
| 1 | `resolverApiBaseUrl`, `aUrlWebSocket`, constantes `API_BASE_URL`/`WS_BASE_URL` | `frontend/src/lib/config.ts` |
| 2 | Tests Vitest de los 4 escenarios + barra final + vacío | `frontend/src/lib/config.test.ts` |
| 3 | `api-client.ts` usa `API_BASE_URL` | `frontend/src/lib/api-client.ts` |
| 4 | `canal-sesion-en-vivo.ts` usa `WS_BASE_URL` (elimina `urlBase()`) | `frontend/src/lib/canal-sesion-en-vivo.ts` |
| 5 | `ARG VITE_API_BASE_URL` en la etapa frontend | `Dockerfile` |
| 6 | Documentar en `.env.example` | `frontend/.env.example` |

Verificación: `tsc -b`, `oxlint`, suite Vitest completa. Sin cambios visuales ni de backend.
