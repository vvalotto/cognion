# Reporte — US-8.1.2: URL base de API y WebSocket resuelta en build

**Estado:** implementada en `feature/US-8.1.1-cors-configurable` (2026-10-16). PR diferido al cierre de la Iteración 1.
**Issue:** #515 · **Spec:** `docs/specs/inc8/US-8.1.2.md`

## Qué se hizo
- `frontend/src/lib/config.ts`: `resolverApiBaseUrl` (env → mismo origen en producción → `localhost:8000` en desarrollo; admite base relativa como `/api`; sin barra final), `aUrlWebSocket` (`http→ws`, `https→wss`), constantes `API_BASE_URL` / `WS_BASE_URL`.
- `api-client.ts` y `canal-sesion-en-vivo.ts` consumen esas constantes; se elimina la duplicación y `urlBase()`.
- `Dockerfile`: `ARG VITE_API_BASE_URL` opcional en la etapa del frontend (vacío = mismo origen).
- `frontend/.env.example` documenta el comportamiento.

## Decisiones
- Sin `.feature` (infra técnica, mismo precedente que US-8.1.1). 8 tests Vitest cubren los 4 escenarios más casos borde.
- El valor por defecto de producción es el **mismo origen**: depende de `US-8.1.6` (servir el frontend desde la imagen) para funcionar de punta a punta.

## Calidad
`tsc -b` y `oxlint` sin errores; Vitest 835/835; cobertura global 93.56 % statements / 86.14 % branches.

## Incidente de proceso
Un `sed` fallido dejó una referencia a `urlBase()` sin reemplazar; `tsc -b` y 25 tests lo detectaron de inmediato y se corrigió antes de commitear.
