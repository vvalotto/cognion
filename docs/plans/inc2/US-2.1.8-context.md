# Contexto de Ejecución — US-2.1.8

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc2/US-2.1.8.md` (Issue #49)
- **Fuente Arquitectura:** `CLAUDE.md` (stack: React 19 + TypeScript + Vite + Tailwind CSS +
  shadcn/ui); infraestructura de routing/cliente API/sesión/`RequireRole` ya establecida por
  `US-1.1.6`/`US-1.1.9` (BC Identidad).

## Historia de Usuario
- **ID:** US-2.1.8
- **Título:** Infraestructura de frontend del Banco de Preguntas
- **Tipo:** Nueva funcionalidad (soporte técnico, sin lógica de dominio propia ni pantalla visible)
- **Puntos:** 3
- **Prioridad:** Alta — primera US frontend de la Iteración 1 del Incremento 2, bloquea
  `US-2.1.9` a `US-2.1.13` (`docs/plans/inc2/inc2-candidatas.md`).

## Adaptación de las fases del skill a stack frontend (TypeScript/React)
Mismo criterio que `US-1.1.6`/`US-1.1.7`/`US-1.1.8`/`US-1.1.9`
(`docs/plans/inc1/US-1.1.9-context.md`) — el skill asume Python (pylint, radon, pytest,
pytest-bdd) en fases 4-7; no aplica a este stack.

| Fase del skill | Equivalente aplicado aquí (frontend) |
|---|---|
| Fase 1 — BDD | `.feature` Gherkin (documental) — implementado como tests Vitest, no step_defs |
| Fase 4/5 — Tests | Vitest + React Testing Library — `banco-preguntas-api.ts` (funciones tipadas, reutilizan `api-client.ts`) y rutas nuevas protegidas por `RequireRole` |
| Fase 6 — Validación BDD | Verificar que los tests Vitest cubren cada escenario del `.feature` |
| Fase 7 — Quality Gates | `npm run lint` (0 errores), `tsc --noEmit` (0 errores), Vitest — cobertura de referencia ≥80% sobre `banco-preguntas-api.ts` y las rutas nuevas de `router.tsx` |

## Decisión de componentes UI (a confirmar en Fase 2)
Sin pantalla propia — placeholders o redirección hasta que `US-2.1.9` a `US-2.1.13` los
reemplacen. No se anticipan componentes UI nuevos.

## Decisiones de Ejecución
- **BDD:** Sí — 2 escenarios Gherkin ya definidos en la spec (ruta protegida por rol, cliente
  API disponible).
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 (4-7 adaptadas a stack frontend, ver tabla)

## Perfil Activo
- **Perfil:** clean-architecture-bc (Cognion) — perfil backend; sin perfil frontend dedicado,
  misma adaptación documentada que en `US-1.1.6`/`US-1.1.7`/`US-1.1.8`/`US-1.1.9`.
- **Patrón arquitectónico:** React 19 + TypeScript + Vite, sin capas Clean Architecture (no
  aplica al frontend). Sin impacto en backend — consume endpoints ya existentes de
  `US-2.1.1` a `US-2.1.7`.
- **Umbrales de calidad (adaptados):**
  - ESLint/oxlint: 0 errores
  - `tsc --noEmit`: 0 errores
  - Vitest: todos los tests pasan, cobertura de referencia ≥80% en `banco-preguntas-api.ts` y
    rutas nuevas

## Rutas de Artefactos
- Contexto: `docs/plans/inc2/US-2.1.8-context.md`
- BDD feature: `tests/features/inc2/US-2.1.8-infra-frontend-banco.feature`
- Plan: `docs/plans/inc2/US-2.1.8-plan.md`
- Reporte: `docs/reports/inc2/US-2.1.8-report.md`
- Quality report: `quality/reports/inc2/US-2.1.8-quality.json`
