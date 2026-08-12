# Contexto de Ejecución — US-1.1.6

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc1/US-1.1.6.md`
- **Fuente Arquitectura:** `CLAUDE.md` (stack: React 19 + TypeScript + Vite + Tailwind CSS +
  shadcn/ui); sin patrón de capas formal para `frontend/` todavía — esta US lo establece
  (routing, cliente API, layouts)

## Historia de Usuario
- **ID:** US-1.1.6
- **Título:** Infraestructura de frontend — routing, cliente API y manejo de sesión
- **Tipo:** Nueva funcionalidad (infraestructura técnica, sin comportamiento de dominio propio)
- **Puntos:** 3
- **Prioridad:** Alta — bloquea US-1.1.7, US-1.1.8, US-1.1.9

## Decisión de alcance tomada con Víctor (2026-07-24)
El proyecto no tenía ninguna estrategia de testing de frontend definida (`package.json` sin
Vitest/Testing Library, CI solo corre ESLint sobre `frontend/`, sin ADR al respecto). Se
decidió **agregar Vitest + React Testing Library ahora**, como parte del alcance de esta US,
en vez de diferirlo — deja el patrón de testing listo para US-1.1.7/1.1.8/1.1.9.

## Adaptación de las fases del skill a stack frontend (TypeScript/React)
El skill `/implement-us` asume Python (pylint, radon, pytest, pytest-bdd) en sus fases 4-7.
Para esta US y las tres siguientes de la Iteración 2, se adapta así:

| Fase del skill | Equivalente Python (backend) | Equivalente aplicado aquí (frontend) |
|---|---|---|
| Fase 1 — BDD | `pytest-bdd`, `.feature` + step_defs | Mismo `.feature` en Gherkin (documentación del comportamiento); implementado como tests Vitest, no step_defs — no existe `pytest-bdd` para TS en este proyecto |
| Fase 4/5 — Tests | `pytest` unit/integration | Vitest + React Testing Library — tests de componentes y del cliente API/sesión |
| Fase 6 — Validación BDD | Ejecutar escenarios `.feature` | Verificar que los tests Vitest cubren cada escenario del `.feature` (sin runner Gherkin dedicado) |
| Fase 7 — Quality Gates | pylint ≥8.0, CC ≤10, MI >20, coverage ≥95% | `npm run lint` (ESLint/oxlint) sin errores, `tsc --noEmit` sin errores, Vitest coverage — umbral de referencia 80% sobre lógica nueva (`api-client.ts`, `session.ts`); no hay umbral formal en `config.json` para frontend, este valor es una convención razonable para este PR, a confirmar/ajustar con Víctor si conviene formalizarlo en un perfil dedicado |

## Alcance acordado con Víctor
- Artefactos de frontend a crear (de la spec):
  - `frontend/src/lib/api-client.ts` — cliente HTTP, adjunta JWT, maneja 401/403
  - `frontend/src/lib/session.ts` — guardar/leer/limpiar JWT y rol
  - `frontend/src/router.tsx` — React Router, rutas placeholder de login/registro
  - `frontend/src/layouts/AuthLayout.tsx`, `AppLayout.tsx`
  - `frontend/package.json` — agrega `react-router`, `vitest`, `@testing-library/react`, `jsdom`
- Sin pantallas de negocio propias — las consumen US-1.1.7/1.1.8/1.1.9.

## Decisiones de Ejecución
- **BDD:** Sí — criterios de aceptación Gherkin ya definidos en la spec (3 escenarios: JWT
  adjuntado, 401 limpia sesión, 403 sin filtrar recurso).
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 (4-7 adaptadas a stack frontend, ver tabla)

## Perfil Activo
- **Perfil:** clean-architecture-bc (Cognion) — perfil backend; sin perfil frontend dedicado,
  se documenta la adaptación en esta US en vez de inventar un perfil nuevo sin aprobación
- **Patrón arquitectónico:** React 19 + TypeScript + Vite, sin capas Clean Architecture (no
  aplica al frontend de este proyecto)
- **Umbrales de calidad (adaptados, ver tabla arriba):**
  - ESLint/oxlint: 0 errores
  - `tsc --noEmit`: 0 errores
  - Vitest: todos los tests pasan, cobertura de referencia ≥80% en lógica nueva

## Rutas de Artefactos
- Contexto: `docs/plans/inc1/US-1.1.6-context.md`
- BDD feature: `tests/features/inc1/US-1.1.6-infraestructura-frontend.feature` (documental —
  implementado como tests Vitest en `frontend/src/lib/*.test.ts`, no step_defs Python)
- Plan: `docs/plans/inc1/US-1.1.6-plan.md`
- Reporte: `docs/reports/inc1/US-1.1.6-report.md`
- Quality report: `quality/reports/inc1/US-1.1.6-quality.json`
