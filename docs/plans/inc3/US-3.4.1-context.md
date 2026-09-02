# Contexto de Ejecución — US-3.4.1

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc3/US-3.4.1.md` (Issue #170)
- **Fuente Arquitectura:** `CLAUDE.md` (stack: React 19 + TypeScript + Vite + Tailwind CSS +
  shadcn/ui); infraestructura de routing/cliente API/sesión/`RequireRole` ya establecida por
  `US-1.1.6`/`US-1.1.9` (BC Identidad). Backend consumido: `src/actividad_evaluativa/frameworks/
  api/{actividades_router,evaluaciones_router,revision_router}.py` (Iteraciones 1 a 3 del
  Incremento 3, `US-3.1.1` a `US-3.3.2`).

## Historia de Usuario
- **ID:** US-3.4.1
- **Título:** Infraestructura de frontend de Actividad Evaluativa
- **Tipo:** Nueva funcionalidad (soporte técnico, sin lógica de dominio propia ni pantalla visible)
- **Puntos:** 3
- **Prioridad:** Alta — primera US frontend de la Iteración 4 del Incremento 3, bloquea
  `US-3.4.2` a `US-3.4.7` (`docs/plans/inc3/inc3-candidatas.md` §Iteración 4).

## Adaptación de las fases del skill a stack frontend (TypeScript/React)
Mismo criterio que `US-2.1.8`/`US-1.1.6` (`docs/plans/inc2/US-2.1.8-context.md`) — el skill
asume Python (pylint, radon, pytest, pytest-bdd) en fases 4-7; no aplica a este stack.

| Fase del skill | Equivalente aplicado aquí (frontend) |
|---|---|
| Fase 1 — BDD | `.feature` Gherkin (documental) — implementado como tests Vitest, no step_defs |
| Fase 4/5 — Tests | Vitest + React Testing Library — `actividad-evaluativa-api.ts` (funciones tipadas, reutilizan `api-client.ts`) y rutas nuevas protegidas por `RequireRole` |
| Fase 6 — Validación BDD | Verificar que los tests Vitest cubren cada escenario del `.feature` |
| Fase 7 — Quality Gates | `npm run lint` (0 errores), `tsc --noEmit` (0 errores), Vitest — cobertura de referencia ≥80% sobre `actividad-evaluativa-api.ts` y las rutas nuevas de `router.tsx` |

## Endpoints backend a cubrir (ya implementados, Iteraciones 1-3)
| Endpoint | Rol | Consumido por |
|---|---|---|
| `POST /actividades` | docente | US-3.4.3 |
| `PATCH /actividades/{id}/periodo` | docente | US-3.4.4 |
| `POST /actividades/{id}/cerrar` | docente | US-3.4.4 |
| `POST /evaluaciones` | estudiante | US-3.4.6 |
| `POST /evaluaciones/{id}/respuestas` | estudiante | US-3.4.6 |
| `POST /evaluaciones/{id}/suspender` | estudiante | US-3.4.6 |
| `POST /evaluaciones/{id}/reanudar` | estudiante | US-3.4.6 |
| `POST /evaluaciones/{id}/finalizar` | estudiante | US-3.4.7 |
| `GET /evaluaciones/{id}/revision` | estudiante | US-3.4.7 |

Sin `GET` de listado/detalle de actividades ni de listado de actividades visibles para
estudiante — gap de backend ya anotado en `inc3-candidatas.md`, a resolver dentro del alcance
de `US-3.4.2`/`US-3.4.4`/`US-3.4.5` (mismo criterio que `US-2.1.9`/`US-2.2.8`). Esta US solo
tipa y expone los endpoints que **ya existen**.

## Decisión de componentes UI (a confirmar en Fase 2)
Sin pantalla propia — placeholders hasta que `US-3.4.2` a `US-3.4.7` los reemplacen (mismo
patrón que `US-2.1.8`). Rutas nuevas: `/actividad-evaluativa/*` (docente) y
`/mis-actividades/*` (estudiante) — primer uso del rol `estudiante` en `RequireRole`.

## Decisiones de Ejecución
- **BDD:** Sí — 3 escenarios Gherkin ya definidos en la spec (ruta docente protegida, ruta
  estudiante protegida, cliente API disponible).
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 (4-7 adaptadas a stack frontend, ver tabla)

## Perfil Activo
- **Perfil:** clean-architecture-bc (Cognion) — perfil backend; sin perfil frontend dedicado,
  misma adaptación documentada que en `US-2.1.8`.
- **Patrón arquitectónico:** React 19 + TypeScript + Vite, sin capas Clean Architecture (no
  aplica al frontend). Sin impacto en backend — consume endpoints ya existentes de
  `US-3.1.1` a `US-3.3.2`.
- **Umbrales de calidad (adaptados):**
  - ESLint/oxlint: 0 errores
  - `tsc --noEmit`: 0 errores
  - Vitest: todos los tests pasan, cobertura de referencia ≥80% en `actividad-evaluativa-api.ts`
    y rutas nuevas

## Rutas de Artefactos
- Contexto: `docs/plans/inc3/US-3.4.1-context.md`
- BDD feature: `tests/features/inc3/US-3.4.1-infra-frontend-actividad-evaluativa.feature`
- Plan: `docs/plans/inc3/US-3.4.1-plan.md`
- Reporte: `docs/reports/inc3/US-3.4.1-report.md`
- Quality report: `quality/reports/inc3/US-3.4.1-quality.json`
