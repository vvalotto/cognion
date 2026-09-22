# Contexto de Ejecución — US-6.3.4

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc6/US-6.3.4.md`
- **Fuente Arquitectura:** Documento local — `CLAUDE.md` (§"Arquitectura interna") + `docs/rf/ARQ_v1.md`

## Historia de Usuario
- **ID:** US-6.3.4
- **Título:** Infraestructura de frontend del modo en vivo
- **Tipo:** Nueva funcionalidad (técnica — primer uso de WebSockets del frontend, sin lógica de dominio propia)
- **Puntos:** 5
- **Prioridad:** Alta — bloquea `US-6.3.5` a `US-6.3.9` (todas las pantallas del modo en vivo)

## Decisiones de Ejecución
- **BDD:** Sí — la spec trae 9 escenarios Gherkin completos
- **skip_bdd:** false (los escenarios se validan con Vitest, mismo criterio que otras US de frontend del proyecto — no hay BDD/pytest-bdd en `frontend/`)
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5 (adaptadas a frontend/Vitest — sin integración HTTP real ni BDD Gherkin ejecutable, se cubre con tests unitarios/componentes), 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc (backend) — para frontend, sigue el patrón ya establecido por `US-2.1.8`/`US-3.4.1`: `lib/*-api.ts` tipado, tests con Vitest, sin arquitectura en capas formal
- **Stack frontend:** React 19 + TypeScript + Vite, Tailwind + shadcn/ui, oxlint, `tsc -b`, Vitest
- **Umbrales de calidad (frontend):** `oxlint` 0 errores, `tsc -b` 0 errores, cobertura ≥ 80% (`vitest.config`)

## Rutas de Artefactos
- Contexto: `docs/plans/inc6/US-6.3.4-context.md`
- Plan: `docs/plans/inc6/US-6.3.4-plan.md`
- Reporte: `docs/reports/inc6/US-6.3.4-report.md`
- Quality report: `quality/reports/inc6/US-6.3.4-quality.json`

## Notas propias de esta US
- **Primer WebSocket del frontend:** el cliente HTTP (`api-client.ts`, JWT, 401/403), `RequireRole` y el patrón de rutas placeholder ya existen — se reutilizan sin cambios (`US-2.1.8`, `US-3.4.1`).
- **Lección `US-ADJ-20` (StrictMode):** el socket debe crearse dentro de `useEffect` y cerrarse en el cleanup — un recurso creado en el render se rompe con el doble montaje de desarrollo, invisible a Vitest. Se verifica en `npm run dev` real.
- **Lección `US-ADJ-23` (`tsc -b`):** el `tsconfig.json` raíz usa `references` con `files: []` — `tsc --noEmit` sin `-b` no detecta errores reales. Usar `tsc -b` (el mismo que corre `npm run build`).
- **Contrato del canal ya definido en la spec** (tabla de mensajes `tipo` → campos) — no hay que inventar el mapeo, está completo en `docs/specs/inc6/US-6.3.4.md`.
- **`jsdom` no trae un `WebSocket` funcional:** los tests necesitan un `WebSocket` falso inyectable.
